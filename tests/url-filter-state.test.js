'use strict';

/**
 * Behavioural tests for the shareable-filter-state feature in solutions.html.
 *
 * The page has no build step, so the URL-state helpers are extracted from the
 * inline <script> and executed against a minimal DOM stub. This verifies the
 * real shipped source rather than a copy of it.
 */

const test = require('node:test');
const assert = require('node:assert');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const SOURCE = fs.readFileSync(path.join(__dirname, '..', 'solutions.html'), 'utf8');

const START_MARKER = '// Legacy short organisation codes';
const END_MARKER = '// Update all filter counts dynamically';

function extractUrlStateSource() {
  const start = SOURCE.indexOf(START_MARKER);
  const end = SOURCE.indexOf(END_MARKER);
  assert.ok(start !== -1, `could not find "${START_MARKER}" in solutions.html`);
  assert.ok(end > start, `could not find "${END_MARKER}" after the URL-state block`);
  return SOURCE.slice(start, end);
}

/** Minimal stand-ins for the handful of DOM features the helpers touch. */
function createCheckbox({ dataset = {}, value = '', checked = false, className = '' }) {
  return { dataset, value, checked, className };
}

function createDom({ checkboxes = {}, inputs = {}, keywords = [], sortOptions = [] } = {}) {
  const elements = new Map();

  for (const [id, value] of Object.entries(inputs)) {
    elements.set(id, { value, checked: false });
  }

  const keywordTags = keywords.map(text => ({ textContent: `${text} ×` }));

  const document = {
    querySelectorAll(selector) {
      if (selector === '.keyword-tag') {
        return keywordTags;
      }
      const checkedOnly = selector.endsWith(':checked');
      const base = checkedOnly ? selector.slice(0, -':checked'.length) : selector;
      const list = checkboxes[base] || [];
      return checkedOnly ? list.filter(item => item.checked) : list;
    },
    getElementById(id) {
      if (!elements.has(id)) {
        elements.set(id, { value: '', checked: false });
      }
      const element = elements.get(id);
      if (id === 'sortSelect' && !element.options) {
        element.options = sortOptions.map(value => ({ value }));
      }
      return element;
    },
  };

  return { document, elements, keywordTags };
}

function loadHelpers(dom, { currentSort = 'updated-desc', pathname = '/solutions.html', search = '' } = {}) {
  const addedKeywords = [];
  const history = { url: null };

  const context = {
    document: dom.document,
    window: {
      location: { pathname, search },
      history: {
        replaceState(_state, _title, url) {
          history.url = url;
        },
      },
    },
    URLSearchParams,
    console,
    currentSort,
    addKeywordTag(keyword) {
      addedKeywords.push(keyword);
      dom.keywordTags.push({ textContent: `${keyword} ×` });
      return true;
    },
  };
  context.globalThis = context;

  vm.createContext(context);
  vm.runInContext(extractUrlStateSource(), context);

  return { context, addedKeywords, history };
}

test('applyFiltersFromUrl does nothing when there is no query string', () => {
  const dom = createDom();
  const { context, addedKeywords } = loadHelpers(dom, { search: '' });

  context.applyFiltersFromUrl();

  assert.deepStrictEqual(addedKeywords, []);
});

test('applyFiltersFromUrl restores keywords, checkboxes, sort and ranges', () => {
  const languageBoxes = [
    createCheckbox({ dataset: { language: 'Python' } }),
    createCheckbox({ dataset: { language: 'R' } }),
  ];
  const tagBoxes = [
    createCheckbox({ dataset: { tag: 'analytics' } }),
    createCheckbox({ dataset: { tag: 'forecasting' } }),
  ];
  const activityBoxes = [
    createCheckbox({ value: 'recent' }),
    createCheckbox({ value: 'stale', checked: true }),
  ];

  const dom = createDom({
    checkboxes: {
      '.language-filter': languageBoxes,
      '.tag-filter': tagBoxes,
      '.activity-filter': activityBoxes,
      '.organisation-filter': [],
    },
    inputs: { publicRepos: '', internalRepos: '', qualityMin: '', starsMin: '' },
    sortOptions: ['updated-desc', 'stars-desc', 'quality-desc'],
  });

  const { context, addedKeywords } = loadHelpers(dom, {
    search: '?q=waiting%20list,triage&lang=Python&tag=analytics&activity=recent&sort=stars-desc&qualityMin=60&visibility=public',
  });

  context.applyFiltersFromUrl();

  assert.deepStrictEqual(addedKeywords, ['waiting list', 'triage']);
  assert.strictEqual(languageBoxes[0].checked, true, 'Python should be selected');
  assert.strictEqual(languageBoxes[1].checked, false, 'R should be untouched');
  assert.strictEqual(tagBoxes[0].checked, true, 'analytics should be selected');
  assert.strictEqual(tagBoxes[1].checked, false, 'forecasting should be untouched');
  assert.strictEqual(activityBoxes[0].checked, true, 'recent activity should be selected');
  assert.strictEqual(activityBoxes[1].checked, false, 'stale should be cleared, not merged');
  assert.strictEqual(context.currentSort, 'stars-desc');
  assert.strictEqual(dom.document.getElementById('qualityMin').value, '60');
  assert.strictEqual(dom.document.getElementById('publicRepos').checked, true);
  assert.strictEqual(dom.document.getElementById('internalRepos').checked, false);
});

test('applyFiltersFromUrl translates legacy short organisation codes', () => {
  const orgBoxes = [
    createCheckbox({ dataset: { organisation: 'Cardiff and Vale UHB' } }),
    createCheckbox({ dataset: { organisation: 'Swansea Bay UHB' } }),
  ];
  const dom = createDom({
    checkboxes: { '.organisation-filter': orgBoxes, '.language-filter': [], '.tag-filter': [] },
  });

  const { context } = loadHelpers(dom, { search: '?org=Cardiff' });
  context.applyFiltersFromUrl();

  assert.strictEqual(orgBoxes[0].checked, true, 'legacy "Cardiff" should map to the full org name');
  assert.strictEqual(orgBoxes[1].checked, false);
});

test('applyFiltersFromUrl ignores a sort value the select does not offer', () => {
  const dom = createDom({
    checkboxes: { '.organisation-filter': [], '.language-filter': [], '.tag-filter': [] },
    sortOptions: ['updated-desc', 'stars-desc'],
  });

  const { context } = loadHelpers(dom, { search: '?sort=javascript:alert(1)' });
  context.applyFiltersFromUrl();

  assert.strictEqual(context.currentSort, 'updated-desc', 'unknown sort keys must be rejected');
});

test('syncUrlWithFilters writes the active filters into the query string', () => {
  const dom = createDom({
    checkboxes: {
      '.organisation-filter': [createCheckbox({ dataset: { organisation: 'Hywel Dda UHB' }, checked: true })],
      '.language-filter': [createCheckbox({ dataset: { language: 'Python' }, checked: true })],
      '.tag-filter': [createCheckbox({ dataset: { tag: 'analytics' }, checked: true })],
      '.activity-filter': [createCheckbox({ value: 'recent', checked: true })],
    },
    inputs: { qualityMin: '70' },
    keywords: ['triage'],
  });
  dom.document.getElementById('publicRepos').checked = true;
  dom.document.getElementById('internalRepos').checked = true;

  const { context, history } = loadHelpers(dom, { currentSort: 'stars-desc' });
  context.syncUrlWithFilters();

  const params = new URLSearchParams(history.url.split('?')[1]);
  assert.strictEqual(params.get('q'), 'triage');
  assert.strictEqual(params.get('org'), 'Hywel Dda UHB');
  assert.strictEqual(params.get('lang'), 'Python');
  assert.strictEqual(params.get('tag'), 'analytics');
  assert.strictEqual(params.get('activity'), 'recent');
  assert.strictEqual(params.get('sort'), 'stars-desc');
  assert.strictEqual(params.get('qualityMin'), '70');
  assert.strictEqual(params.get('visibility'), null, 'both visibilities on is the default, so it is omitted');
});

test('syncUrlWithFilters clears the query string when no filters are active', () => {
  const dom = createDom({
    checkboxes: {
      '.organisation-filter': [],
      '.language-filter': [],
      '.tag-filter': [],
      '.activity-filter': [],
    },
  });
  dom.document.getElementById('publicRepos').checked = true;
  dom.document.getElementById('internalRepos').checked = true;

  const { context, history } = loadHelpers(dom);
  context.syncUrlWithFilters();

  assert.strictEqual(history.url, '/solutions.html', 'a cleared view should have a bare path');
});

test('restoring filters does not rewrite the URL mid-flight', () => {
  const dom = createDom({
    checkboxes: { '.organisation-filter': [], '.language-filter': [], '.tag-filter': [] },
  });

  const { context, history } = loadHelpers(dom, { search: '?lang=Python' });

  // addKeywordTag normally triggers a re-render; prove the guard holds.
  context.addKeywordTag = keyword => {
    context.syncUrlWithFilters();
    dom.keywordTags.push({ textContent: `${keyword} ×` });
    return true;
  };
  context.applyFiltersFromUrl();

  assert.strictEqual(history.url, null, 'no history write should happen while restoring');
});

test('a filter state survives a full round trip through the URL', () => {
  const makeBoxes = () => ({
    '.organisation-filter': [
      createCheckbox({ dataset: { organisation: 'Public Health Wales' } }),
      createCheckbox({ dataset: { organisation: 'Powys Teaching Health Board' } }),
    ],
    '.language-filter': [createCheckbox({ dataset: { language: 'Python' } })],
    '.tag-filter': [createCheckbox({ dataset: { tag: 'analytics' } })],
    '.activity-filter': [createCheckbox({ value: 'recent' })],
  });

  // Build a state, serialise it.
  const first = makeBoxes();
  first['.organisation-filter'][0].checked = true;
  first['.language-filter'][0].checked = true;
  first['.activity-filter'][0].checked = true;

  const writeDom = createDom({ checkboxes: first, inputs: { starsMin: '5' }, keywords: ['triage'] });
  writeDom.document.getElementById('publicRepos').checked = true;
  writeDom.document.getElementById('internalRepos').checked = false;

  const { context: writer, history } = loadHelpers(writeDom, { currentSort: 'quality-desc' });
  writer.syncUrlWithFilters();

  // Replay it into a fresh page.
  const second = makeBoxes();
  const readDom = createDom({
    checkboxes: second,
    sortOptions: ['updated-desc', 'quality-desc'],
  });
  const search = history.url.slice(history.url.indexOf('?'));
  const { context: reader, addedKeywords } = loadHelpers(readDom, { search });
  reader.applyFiltersFromUrl();

  assert.deepStrictEqual(addedKeywords, ['triage']);
  assert.strictEqual(second['.organisation-filter'][0].checked, true);
  assert.strictEqual(second['.organisation-filter'][1].checked, false);
  assert.strictEqual(second['.language-filter'][0].checked, true);
  assert.strictEqual(second['.activity-filter'][0].checked, true);
  assert.strictEqual(reader.currentSort, 'quality-desc');
  assert.strictEqual(readDom.document.getElementById('starsMin').value, '5');
  assert.strictEqual(readDom.document.getElementById('publicRepos').checked, true);
  assert.strictEqual(readDom.document.getElementById('internalRepos').checked, false);
});
