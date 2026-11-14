'use strict';

/**
 * Guards the inline <script> blocks in the static pages.
 *
 * These pages have no build step, no module system and no browser-based test
 * run, so a call to a function that was renamed or deleted fails only at
 * runtime in a user's browser. These tests check two invariants cheaply:
 *
 *   1. every inline script block parses, and
 *   2. every function call resolves to something that actually exists --
 *      either a function declared in the page or a known browser/library
 *      global.
 */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const PAGES = ['index.html', 'solutions.html', 'solution.html', 'guides.html', 'service-metrics.html'];

// <script> blocks without a src attribute, i.e. page-local code.
const INLINE_SCRIPT_RE = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;

/** Globals supplied by the browser, Bootstrap, Chart.js or js/security.js. */
const KNOWN_GLOBALS = new Set([
  // Language / standard library
  'Array', 'Boolean', 'Date', 'Error', 'Function', 'Intl', 'JSON', 'Map', 'Math',
  'Number', 'Object', 'Promise', 'RegExp', 'Set', 'String', 'Symbol', 'parseFloat',
  'parseInt', 'isNaN', 'isFinite', 'decodeURIComponent', 'encodeURIComponent',
  'decodeURI', 'encodeURI', 'URL', 'URLSearchParams', 'Intl',
  // DOM / BOM
  'alert', 'confirm', 'prompt', 'fetch', 'setTimeout', 'setInterval',
  'clearTimeout', 'clearInterval', 'requestAnimationFrame', 'getComputedStyle',
  'document', 'window', 'console', 'history', 'location', 'navigator',
  'CustomEvent', 'Event', 'IntersectionObserver', 'MutationObserver',
  // Third-party libraries loaded via <script src>
  'bootstrap', 'Chart', 'jQuery', '$',
  // js/security.js
  'escapeHtml', 'escapeJsString', 'safeUrl',
  // Control-flow keywords that look like calls to a naive regex
  'if', 'for', 'while', 'switch', 'catch', 'return', 'typeof', 'function',
  'await', 'new', 'else', 'do', 'in', 'of', 'delete', 'void', 'case', 'yield',
]);

function readPage(page) {
  return fs.readFileSync(path.join(ROOT, page), 'utf8');
}

function inlineScripts(html) {
  return Array.from(html.matchAll(INLINE_SCRIPT_RE)).map(match => match[1]);
}

/**
 * Names that are callable within the page: function declarations, plus
 * function-valued const/let/var bindings.
 */
function declaredCallables(source) {
  const names = new Set();

  for (const match of source.matchAll(/\bfunction\s+([A-Za-z_$][\w$]*)\s*\(/g)) {
    names.add(match[1]);
  }
  // const foo = function (...) / const foo = (...) => / const foo = async (...) =>
  const assigned =
    /\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function\b|\([^)]*\)\s*=>|[A-Za-z_$][\w$]*\s*=>)/g;
  for (const match of source.matchAll(assigned)) {
    names.add(match[1]);
  }
  return names;
}

/**
 * Replaces the *text* of string and template literals with spaces, while
 * keeping the code inside `${...}` interpolations. Without this, ordinary
 * prose such as `"Repositories (12)"` or a CSS colour like `'rgba(0,0,0,.5)'`
 * looks exactly like a function call.
 */
function stripStringLiterals(source) {
  let out = '';
  let i = 0;
  // Stack of open template literals, so nested `${ `...` }` is handled.
  const templateDepths = [];
  let braceDepth = 0;

  while (i < source.length) {
    const ch = source[i];

    if (ch === "'" || ch === '"') {
      const quote = ch;
      out += ' ';
      i += 1;
      while (i < source.length && source[i] !== quote) {
        if (source[i] === '\\') {
          i += 1;
        }
        if (source[i] === '\n') {
          break;
        }
        out += ' ';
        i += 1;
      }
      out += ' ';
      i += 1;
      continue;
    }

    if (ch === '`') {
      templateDepths.push(braceDepth);
      out += ' ';
      i += 1;
      // Consume literal text until the template closes or an interpolation opens.
      while (i < source.length) {
        if (source[i] === '\\') {
          out += '  ';
          i += 2;
          continue;
        }
        if (source[i] === '`') {
          templateDepths.pop();
          out += ' ';
          i += 1;
          break;
        }
        if (source[i] === '$' && source[i + 1] === '{') {
          out += '  ';
          i += 2;
          braceDepth += 1;
          break;
        }
        out += source[i] === '\n' ? '\n' : ' ';
        i += 1;
      }
      continue;
    }

    if (ch === '}' && templateDepths.length > 0 && braceDepth === templateDepths[templateDepths.length - 1] + 1) {
      // End of an interpolation: resume literal text of the enclosing template.
      braceDepth -= 1;
      out += ' ';
      i += 1;
      while (i < source.length) {
        if (source[i] === '\\') {
          out += '  ';
          i += 2;
          continue;
        }
        if (source[i] === '`') {
          templateDepths.pop();
          out += ' ';
          i += 1;
          break;
        }
        if (source[i] === '$' && source[i + 1] === '{') {
          out += '  ';
          i += 2;
          braceDepth += 1;
          break;
        }
        out += source[i] === '\n' ? '\n' : ' ';
        i += 1;
      }
      continue;
    }

    if (ch === '{') {
      braceDepth += 1;
    } else if (ch === '}') {
      braceDepth -= 1;
    }

    out += ch;
    i += 1;
  }

  return out;
}

/**
 * Bare `name(` call sites. Method calls (`foo.bar(`), property definitions and
 * declarations are excluded so that only unqualified references remain -- those
 * are the ones that throw a ReferenceError when the target does not exist.
 */
function calledNames(source) {
  const withoutComments = stripStringLiterals(source)
    .replace(/\/\*[\s\S]*?\*\//g, ' ')
    .replace(/(^|[^:])\/\/[^\n]*/g, '$1');

  const names = new Set();
  const callRe = /(^|[^\w$.?])([A-Za-z_$][\w$]*)\s*\(/g;
  for (const match of withoutComments.matchAll(callRe)) {
    const name = match[2];
    // Skip declarations such as `function foo(` and `class Foo(`.
    const preceding = withoutComments.slice(Math.max(0, match.index - 12), match.index + match[1].length);
    if (/\b(?:function|class)\s*$/.test(preceding)) {
      continue;
    }
    names.add(name);
  }
  return names;
}

for (const page of PAGES) {
  test(`${page}: every inline script parses`, () => {
    const scripts = inlineScripts(readPage(page));
    assert.ok(scripts.length > 0, `${page} should contain at least one inline script`);

    scripts.forEach((source, index) => {
      assert.doesNotThrow(
        () => new vm.Script(source),
        `inline script #${index} in ${page} is not valid JavaScript`
      );
    });
  });

  test(`${page}: every called function is defined`, () => {
    const html = readPage(page);
    const combined = inlineScripts(html).join('\n');

    const declared = declaredCallables(combined);
    const missing = [];

    for (const name of calledNames(combined)) {
      if (!declared.has(name) && !KNOWN_GLOBALS.has(name)) {
        missing.push(name);
      }
    }

    assert.deepStrictEqual(
      missing.sort(),
      [],
      `${page} calls function(s) that are never defined: ${missing.join(', ')}`
    );
  });
}

test('solutions.html wires up URL-based filter state', () => {
  const html = readPage('solutions.html');
  const combined = inlineScripts(html).join('\n');

  assert.ok(
    /function\s+applyFiltersFromUrl\s*\(/.test(combined),
    'applyFiltersFromUrl should be defined'
  );
  assert.ok(
    /function\s+syncUrlWithFilters\s*\(/.test(combined),
    'syncUrlWithFilters should be defined'
  );
  assert.ok(
    /\bapplyFiltersFromUrl\(\)/.test(combined),
    'applyFiltersFromUrl should be called when the page loads'
  );
  assert.ok(
    /\bsyncUrlWithFilters\(\)/.test(combined),
    'syncUrlWithFilters should be called when results are rendered'
  );
  assert.ok(
    !/handleUrlParameters/.test(combined),
    'the replaced handleUrlParameters helper should no longer be referenced'
  );
});

test('every page exposes a skip link targeting its main landmark', () => {
  for (const page of PAGES) {
    const html = readPage(page);
    assert.ok(
      /<a[^>]*class="skip-link"[^>]*href="#main-content"/.test(html),
      `${page} should start with a skip link`
    );
    assert.ok(
      /<main[^>]*id="main-content"/.test(html),
      `${page} should have a <main id="main-content"> landmark`
    );
    assert.strictEqual(
      (html.match(/<main\b/g) || []).length,
      1,
      `${page} should have exactly one <main> landmark`
    );
    assert.strictEqual(
      (html.match(/<\/main>/g) || []).length,
      1,
      `${page} should close its <main> landmark exactly once`
    );
  }
});
