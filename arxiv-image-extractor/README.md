# arXiv Image Extractor

A simple web tool to extract and display all images from arXiv HTML papers in a beautiful grid layout.

## Features

- Extract all images from any arXiv HTML page
- Display images in a responsive grid
- View full-size images in a new tab
- Download individual images
- Automatic filtering of tiny icons
- Beautiful gradient UI with hover effects

## Usage

1. Open `index.html` in your web browser
2. Paste an arXiv HTML URL (e.g., `https://arxiv.org/html/2510.21986v1`)
3. Click "Extract Images" or press Enter
4. Browse the extracted images in the grid
5. Click "Open" to view full-size or "Download" to save locally

## How It Works

The tool uses a CORS proxy (allorigins.win) to fetch the arXiv HTML page, parses it to find all image elements, converts relative URLs to absolute ones, filters out small icons, and displays the results in a responsive grid.

## Examples

Try these arXiv papers:
- https://arxiv.org/html/2510.21986v1
- https://arxiv.org/html/2312.11805v3
- Any other arXiv HTML paper URL

## Technical Details

- Pure HTML/CSS/JavaScript (no dependencies)
- Client-side processing
- Uses DOMParser for HTML parsing
- Responsive grid layout with CSS Grid
- CORS proxy for cross-origin requests

## Notes

- Only works with arXiv HTML format papers (not PDF links)
- Filters out images smaller than 50x50px to exclude icons
- Images are lazy-loaded for better performance
