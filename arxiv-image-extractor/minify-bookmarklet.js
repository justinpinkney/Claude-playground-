const fs = require('fs');

// Read the bookmarklet source
const source = fs.readFileSync('bookmarklet.js', 'utf8');

// Safer minification that preserves template literals and URLs
let minified = source
    // Remove line comments (only at start of line after optional whitespace)
    .replace(/^\s*\/\/.*$/gm, '')
    // Remove multi-line comments
    .replace(/\/\*[\s\S]*?\*\//g, '')
    // Remove inline comments (// after code, but not in URLs)
    // Match space(s) + // + rest of line, but only when // is not preceded by : or /
    .replace(/(?<![:\/])\s+\/\/[^\n]*$/gm, '')
    // Remove empty lines
    .replace(/^\s*\n/gm, '')
    // Remove leading whitespace from each line
    .replace(/^\s+/gm, '')
    // Replace multiple spaces with single space
    .replace(/ +/g, ' ')
    // Remove newlines (replace with nothing, spaces already handled)
    .replace(/\n/g, '')
    .trim();

// URL encode for bookmarklet
const encoded = 'javascript:' + encodeURIComponent(minified)
    .replace(/'/g, '%27')
    .replace(/"/g, '%22');

// Read the HTML template
let html = fs.readFileSync('bookmarklet.html', 'utf8');

// Replace the bookmarklet href (find the href attribute and replace it)
html = html.replace(/href="javascript:[^"]*"/, `href="${encoded}"`);

// Write back
fs.writeFileSync('bookmarklet.html', html);

console.log('Bookmarklet minified and updated in bookmarklet.html');
console.log(`Minified size: ${encoded.length} characters`);
