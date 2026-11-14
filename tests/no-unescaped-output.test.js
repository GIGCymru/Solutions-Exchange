/**
 * Guard against unescaped repository data being interpolated into HTML.
 *
 * Repository names, descriptions, topics and URLs come from the GitHub API and
 * are controlled by repository owners. Every interpolation of that data into an
 * innerHTML template must pass through escapeHtml()/safeUrl() (see js/security.js).
 *
 * Run with: node --test tests/
 */
const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const PAGES = ['index.html', 'solutions.html', 'guides.html', 'service-metrics.html', 'solution.html'];

// Expressions that render untrusted, API-sourced values. Bare identifiers use a
// negative lookahead so `tags.map(`, `orgsCount` and `tag.replace(` are not matched.
const UNTRUSTED = new RegExp(
    '\\$\\{\\s*(' +
        'repo\\.[a-zA-Z_]+|story\\.[a-zA-Z_]+|getOrganisationFullName\\(|' +
        '(?:tag|lang|org|keyword|tagName|license|cardImage|qualityScore|timeSinceUpdate)(?![\\w.])' +
    ')',
    'g'
);

// Interpolations that cannot inject markup because they only ever emit one of
// two hard-coded literals. Kept deliberately narrow.
const SAFE_PATTERNS = [
    /^\$\{\s*repo\.(featured|private)\s*\?\s*'/,
    // The opening of a .map() whose body escapes each tag separately.
    /^\$\{\s*story\.tags\s*\?\s*story\.tags\.map\(/,
];

function isEscaped(line, index) {
    // Look at the characters immediately before the interpolation for a call to
    // one of the escaping helpers.
    const prefix = line.slice(0, index);
    return /(escapeHtml|escapeJsString|safeUrl)\s*\(\s*$/.test(prefix);
}

// `document.title` and `textContent` assign text, never markup, so the browser
// cannot be tricked into parsing injected HTML from them. `innerHTML`,
// `outerHTML`, `insertAdjacentHTML` and attribute values are deliberately not
// treated as text sinks.
function isTextSink(line, index) {
    return /(document\.title|\.textContent)\s*=\s*[^=]*$/.test(line.slice(0, index));
}

for (const page of PAGES) {
    test(`${page} escapes all repository-sourced output`, () => {
        const contents = fs.readFileSync(path.join(ROOT, page), 'utf8');
        const offenders = [];

        contents.split('\n').forEach((line, lineNumber) => {
            for (const match of line.matchAll(UNTRUSTED)) {
                const expression = line.slice(match.index);

                if (SAFE_PATTERNS.some((pattern) => pattern.test(expression))) {
                    continue;
                }
                // `${escapeHtml(repo.name)}` -> the inner match starts after the call.
                if (isEscaped(line, match.index + 2)) {
                    continue;
                }
                if (isTextSink(line, match.index)) {
                    continue;
                }
                offenders.push(`${page}:${lineNumber + 1}: ${line.trim()}`);
            }
        });

        assert.deepStrictEqual(
            offenders,
            [],
            `Unescaped repository data found. Wrap these in escapeHtml() or safeUrl():\n${offenders.join('\n')}`
        );
    });

    test(`${page} loads the escaping helpers`, () => {
        const contents = fs.readFileSync(path.join(ROOT, page), 'utf8');
        assert.ok(
            contents.includes('js/security.js'),
            `${page} must load js/security.js before rendering repository data`
        );
    });
}

test('no inline onclick handlers interpolate repository data', () => {
    for (const page of PAGES) {
        const contents = fs.readFileSync(path.join(ROOT, page), 'utf8');
        const inlineHandlers = contents.match(/on(click|error|load|mouseover)="[^"]*\$\{[^"]*"/g) || [];
        assert.deepStrictEqual(
            inlineHandlers,
            [],
            `${page} must use data attributes and delegated listeners instead of inline handlers: ${inlineHandlers}`
        );
    }
});
