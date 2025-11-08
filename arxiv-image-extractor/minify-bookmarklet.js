const fs = require('fs');

// Read the bookmarklet source
const source = fs.readFileSync('bookmarklet.js', 'utf8');

// Extract the function content (remove comments and minify)
let minified = source
    // Remove line comments
    .replace(/\/\/.*$/gm, '')
    // Remove multi-line comments
    .replace(/\/\*[\s\S]*?\*\//g, '')
    // Remove extra whitespace
    .replace(/\s+/g, ' ')
    // Remove spaces around operators and punctuation
    .replace(/\s*([{}();,:])\s*/g, '$1')
    // Remove spaces around operators
    .replace(/\s*([=+\-*/<>!&|])\s*/g, '$1')
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
