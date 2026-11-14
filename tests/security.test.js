/**
 * Tests for the output escaping helpers.
 * Run with: node --test tests/
 */
const test = require('node:test');
const assert = require('node:assert');

const { escapeHtml, escapeJsString, safeUrl } = require('../js/security.js');

test('escapeHtml neutralises script injection in descriptions', () => {
    const malicious = '<img src=x onerror="alert(1)">';
    const escaped = escapeHtml(malicious);

    assert.ok(!escaped.includes('<img'));
    assert.strictEqual(escaped, '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
});

test('escapeHtml escapes quotes so attribute values cannot break out', () => {
    assert.strictEqual(escapeHtml('" onmouseover="alert(1)'), '&quot; onmouseover=&quot;alert(1)');
    assert.strictEqual(escapeHtml("it's"), 'it&#39;s');
});

test('escapeHtml handles null, undefined and non-strings', () => {
    assert.strictEqual(escapeHtml(null), '');
    assert.strictEqual(escapeHtml(undefined), '');
    assert.strictEqual(escapeHtml(42), '42');
});

test('escapeHtml escapes ampersands first to avoid double-decoding', () => {
    assert.strictEqual(escapeHtml('&lt;'), '&amp;lt;');
});

test('escapeJsString prevents breaking out of an inline handler', () => {
    const malicious = "'); alert(1); //";
    const escaped = escapeJsString(malicious);

    // The escaped value must parse back to the original string, proving the
    // quote cannot terminate the literal early.
    const roundTrip = new Function(`return '${escaped}'`)();
    assert.strictEqual(roundTrip, malicious);
});

test('escapeJsString escapes closing script tags and newlines', () => {
    assert.ok(!escapeJsString('</script>').includes('<'));
    assert.strictEqual(escapeJsString('a\nb'), 'a\\nb');
    assert.strictEqual(new Function(`return '${escapeJsString('a\nb')}'`)(), 'a\nb');
});

test('escapeJsString round-trips backslashes', () => {
    const value = 'back\\slash';
    assert.strictEqual(new Function(`return '${escapeJsString(value)}'`)(), value);
});

test('safeUrl blocks dangerous schemes', () => {
    assert.strictEqual(safeUrl('javascript:alert(1)'), '#');
    assert.strictEqual(safeUrl('JaVaScRiPt:alert(1)'), '#');
    assert.strictEqual(safeUrl('data:text/html,<script>alert(1)</script>'), '#');
    assert.strictEqual(safeUrl('vbscript:msgbox(1)'), '#');
});

test('safeUrl blocks schemes obfuscated with control characters', () => {
    assert.strictEqual(safeUrl('java\u0009script:alert(1)'), '#');
    assert.strictEqual(safeUrl('java\u0000script:alert(1)'), '#');
});

test('safeUrl allows normal repository and relative links', () => {
    assert.strictEqual(safeUrl('https://github.com/GIGCymru/repo'), 'https://github.com/GIGCymru/repo');
    assert.strictEqual(safeUrl('guides.html#signup'), 'guides.html#signup');
    assert.strictEqual(safeUrl('mailto:someone@wales.nhs.uk'), 'mailto:someone@wales.nhs.uk');
});

test('safeUrl escapes quotes in otherwise valid URLs', () => {
    assert.ok(!safeUrl('https://example.com/"onmouseover="alert(1)').includes('"'));
});

test('safeUrl returns the supplied fallback for empty values', () => {
    assert.strictEqual(safeUrl('', 'index.html'), 'index.html');
    assert.strictEqual(safeUrl(null), '#');
});
