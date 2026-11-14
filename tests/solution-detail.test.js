'use strict';

/**
 * Renders the solution detail page's template in isolation.
 *
 * solution.html publishes owner-controlled values (repository names,
 * descriptions and the contents of a team's solution.json), so this exercises
 * the real template against hostile input as well as checking that optional
 * metadata degrades gracefully.
 */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const ROOT = path.join(__dirname, '..');
const security = require(path.join(ROOT, 'js', 'security.js'));

const HTML = fs.readFileSync(path.join(ROOT, 'solution.html'), 'utf8');
const INLINE_SCRIPT_RE = /<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;

function loadPageScript() {
  // The last inline block is the page logic; earlier ones are analytics.
  const blocks = Array.from(HTML.matchAll(INLINE_SCRIPT_RE)).map(match => match[1]);
  const source = blocks[blocks.length - 1];
  assert.ok(/function renderSolution/.test(source), 'expected to find the page script');

  const listeners = [];
  const context = {
    console,
    URLSearchParams,
    escapeHtml: security.escapeHtml,
    safeUrl: security.safeUrl,
    document: {
      addEventListener(name, handler) {
        listeners.push([name, handler]);
      },
      getElementById: () => ({ textContent: '', innerHTML: '', appendChild() {} }),
    },
    window: { location: { search: '' } },
    fetch: () => Promise.reject(new Error('not used')),
  };
  context.globalThis = context;

  vm.createContext(context);
  vm.runInContext(source, context);
  return { context, listeners };
}

function baseRepo(overrides = {}) {
  return Object.assign(
    {
      name: 'ed-forecast',
      full_name: 'DHCW-Digital-Health-and-Care-Wales/ed-forecast',
      description: 'Forecasts emergency department attendance.',
      html_url: 'https://github.com/DHCW-Digital-Health-and-Care-Wales/ed-forecast',
      private: false,
      owner: { login: 'DHCW-Digital-Health-and-Care-Wales' },
      language: 'Python',
      license: { name: 'MIT Licence' },
      topics: ['nhs', 'forecasting'],
      all_tags: ['nhs', 'forecasting', 'Python'],
      stargazers_count: 12,
      forks_count: 3,
      quality_score: 85,
      updated_at: '2026-01-15T09:00:00Z',
    },
    overrides
  );
}

test('renders the core repository details', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(baseRepo());

  assert.match(html, /ed-forecast/);
  assert.match(html, /Forecasts emergency department attendance\./);
  assert.match(html, /Digital Health and Care Wales/);
  assert.match(html, /MIT Licence/);
  assert.match(html, /PUBLIC/);
  assert.match(html, /Quality: 85\/100/);
  assert.match(html, /15\/01\/2026/);
});

test('escapes hostile repository fields', () => {
  const { context } = loadPageScript();
  const payload = '<img src=x onerror=alert(1)>';
  const html = context.renderSolution(
    baseRepo({
      name: payload,
      description: `"><script>alert('xss')</script>`,
      all_tags: [payload],
      license: { name: payload },
    })
  );

  assert.ok(!html.includes('<img src=x'), 'the raw image payload must not survive');
  assert.ok(!html.includes('<script>alert'), 'the raw script payload must not survive');
  assert.match(html, /&lt;img src=x/, 'the payload should appear escaped instead');
});

test('escapes hostile solution.json metadata', () => {
  const { context } = loadPageScript();
  const payload = '<svg onload=alert(1)>';
  const html = context.renderSolution(
    baseRepo({
      solution_metadata: {
        contact: 'team@wales.nhs.uk',
        summary: payload,
        problem: payload,
        benefits: [payload],
        dependencies: [payload],
        clinical_safety: payload,
        information_governance: payload,
      },
    })
  );

  assert.ok(!html.includes('<svg onload'), 'metadata must be escaped too');
  assert.match(html, /&lt;svg onload/);
});

test('refuses a javascript: URL supplied as a repository or metadata link', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(
    baseRepo({
      html_url: 'javascript:alert(1)',
      solution_metadata: {
        contact: 'team@wales.nhs.uk',
        documentation_url: 'javascript:alert(2)',
        demo_url: 'javascript:alert(3)',
      },
    })
  );

  assert.ok(!/href="javascript:/.test(html), 'javascript: URLs must be neutralised');
});

test('omits metadata sections a team has not filled in', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(baseRepo());

  assert.ok(!html.includes('Problem it solves'), 'absent fields should not render empty headings');
  assert.ok(!html.includes('Benefits'));
  assert.ok(!html.includes('Clinical safety'));
  assert.match(html, /has not published a/, 'should prompt the owner to add solution.json');
});

test('shows metadata sections when they are provided', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(
    baseRepo({
      solution_metadata: {
        contact: 'team@wales.nhs.uk',
        lifecycle: 'live',
        support: 'best-effort',
        problem: 'Rotas were planned by hand.',
        benefits: ['Saves time'],
        clinical_safety: 'DCB0129 assessment complete',
      },
    })
  );

  assert.match(html, /Problem it solves/);
  assert.match(html, /Rotas were planned by hand\./);
  assert.match(html, /Saves time/);
  assert.match(html, /DCB0129 assessment complete/);
  assert.match(html, /Best effort/, 'support codes should be shown as readable labels');
  assert.match(html, /lifecycle-badge/);
  assert.ok(!html.includes('has not published a'), 'the prompt should disappear once metadata exists');
});

test('links an email contact as mailto and a GitHub handle as a profile', () => {
  const { context } = loadPageScript();

  const emailHtml = context.renderSolution(
    baseRepo({ solution_metadata: { contact: 'team@wales.nhs.uk' } })
  );
  assert.match(emailHtml, /href="mailto:team@wales\.nhs\.uk"/);

  const handleHtml = context.renderSolution(
    baseRepo({ solution_metadata: { contact: '@jane-doe' } })
  );
  assert.match(handleHtml, /href="https:\/\/github\.com\/jane-doe"/);
});

test('lists reuse contacts alongside the primary contact without duplicating it', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(
    baseRepo({
      solution_metadata: {
        contact: 'team@wales.nhs.uk',
        reuse_contacts: ['team@wales.nhs.uk', '@jane-doe'],
      },
    })
  );

  assert.strictEqual(
    (html.match(/mailto:team@wales\.nhs\.uk/g) || []).length,
    1,
    'the primary contact should appear once'
  );
  assert.match(html, /jane-doe/);
});

test('marks a private solution as internal and offers a request-access route', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(baseRepo({ private: true }));

  assert.match(html, /INTERNAL/);
  assert.match(html, /Request access/);
});

test('tags link back to a pre-filtered Solutions Exchange view', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution(baseRepo({ all_tags: ['data science'] }));

  assert.match(html, /solutions\.html\?tag=data%20science/);
});

test('copes with a sparse record that is missing optional fields', () => {
  const { context } = loadPageScript();
  const html = context.renderSolution({
    name: 'bare-repo',
    full_name: 'GIGCymru/bare-repo',
    private: false,
    owner: { login: 'GIGCymru' },
    html_url: 'https://github.com/GIGCymru/bare-repo',
  });

  assert.match(html, /bare-repo/);
  assert.match(html, /No description has been provided/);
  assert.match(html, /Not specified/, 'a missing licence should be labelled');
  assert.match(html, /No tags have been applied/);
  assert.match(html, /Unknown/, 'a missing updated_at should not render an invalid date');
  assert.ok(!html.includes('NaN'), 'no NaN should leak into the page');
  assert.ok(!html.includes('undefined'), 'no undefined should leak into the page');
});
