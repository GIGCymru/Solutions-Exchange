/**
 * NHS Wales Solutions Exchange - output escaping helpers.
 *
 * Repository data (names, descriptions, topics, URLs) comes from the GitHub API
 * and is controlled by the teams that own each repository. It must never be
 * injected into the DOM as raw HTML, so every template interpolation goes
 * through these helpers.
 */
(function (global) {
    'use strict';

    var HTML_ENTITIES = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#39;',
        '`': '&#96;'
    };

    /**
     * Escape a value for safe interpolation into HTML text or a quoted attribute.
     * @param {*} value
     * @returns {string}
     */
    function escapeHtml(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value).replace(/[&<>"'`]/g, function (character) {
            return HTML_ENTITIES[character];
        });
    }

    /**
     * Escape a value for use inside a single-quoted JavaScript string literal
     * within an HTML attribute (for example an inline onclick handler).
     * @param {*} value
     * @returns {string}
     */
    function escapeJsString(value) {
        if (value === null || value === undefined) {
            return '';
        }
        return String(value)
            .replace(/\\/g, '\\\\')
            .replace(/'/g, "\\'")
            .replace(/"/g, '\\"')
            .replace(/\n/g, '\\n')
            .replace(/\r/g, '\\r')
            .replace(/</g, '\\u003C')
            .replace(/>/g, '\\u003E')
            .replace(/&/g, '\\u0026');
    }

    /**
     * Return a URL only when it uses a safe scheme, blocking javascript: and
     * data: URLs that would otherwise execute when a link is clicked.
     * @param {*} value
     * @param {string} [fallback='#']
     * @returns {string} an HTML-escaped, safe URL
     */
    function safeUrl(value, fallback) {
        var replacement = fallback === undefined ? '#' : fallback;
        if (!value) {
            return replacement;
        }

        var raw = String(value).trim();
        // Strip control characters used to smuggle "java\tscript:" past checks.
        var normalised = raw.replace(/[\u0000-\u001F\u007F]/g, '').toLowerCase();

        // Allow relative URLs, but only permit explicitly safe schemes.
        var scheme = normalised.match(/^([a-z][a-z0-9+.\-]*):/);
        if (scheme && ['http', 'https', 'mailto'].indexOf(scheme[1]) === -1) {
            return replacement;
        }

        return escapeHtml(raw);
    }

    var api = {
        escapeHtml: escapeHtml,
        escapeJsString: escapeJsString,
        safeUrl: safeUrl
    };

    global.SolutionsExchangeSecurity = api;

    // Convenience globals so inline templates stay readable.
    global.escapeHtml = escapeHtml;
    global.escapeJsString = escapeJsString;
    global.safeUrl = safeUrl;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    }
})(typeof window !== 'undefined' ? window : this);
