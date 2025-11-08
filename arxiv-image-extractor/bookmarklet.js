// arXiv Image Extractor Bookmarklet with Are.na Integration
// This is the readable version. See bookmarklet.html for the minified bookmarklet to drag to your bookmarks bar.

(async function() {
    // Check if we're on an arXiv page
    const currentUrl = window.location.href;
    const arxivMatch = currentUrl.match(/arxiv\.org\/(abs|pdf|html)\/(\d+\.\d+)/);

    if (!arxivMatch) {
        alert('Please run this bookmarklet on an arXiv page');
        return;
    }

    const paperId = arxivMatch[2];
    const htmlUrl = `https://arxiv.org/html/${paperId}`;
    let paperTitle = '';

    // Load saved Are.na config
    const savedToken = localStorage.getItem('arenaToken') || '';
    const savedChannel = localStorage.getItem('arenaChannel') || '';

    // Create overlay
    const overlay = document.createElement('div');
    overlay.id = 'arxiv-image-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: white;
        z-index: 999999;
        overflow-y: auto;
        padding: 20px;
        font-family: monospace;
    `;

    overlay.innerHTML = `
        <div style="border: 2px solid black; padding: 20px; margin-bottom: 20px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h1 style="margin: 0; font-size: 24px;">arXiv Images: ${paperId}</h1>
                <button id="close-overlay" style="padding: 10px 20px; background: black; color: white; border: 2px solid black; font-family: monospace; cursor: pointer; font-size: 14px;">Close</button>
            </div>
            <div style="border-top: 2px solid black; padding-top: 15px; margin-bottom: 10px;">
                <div style="font-size: 14px; font-weight: bold; margin-bottom: 10px;">Are.na Configuration</div>
                <div style="display: flex; gap: 10px; margin-bottom: 5px;">
                    <input id="arena-token" type="text" placeholder="Are.na API Token" value="${savedToken}" autocomplete="off" spellcheck="false" tabindex="1" style="flex: 1; padding: 8px; border: 2px solid black; font-size: 12px; font-family: monospace; background: white; cursor: text;">
                    <input id="arena-channel" type="text" placeholder="Channel Slug" value="${savedChannel}" autocomplete="off" spellcheck="false" tabindex="2" style="flex: 1; padding: 8px; border: 2px solid black; font-size: 12px; font-family: monospace; background: white; cursor: text;">
                </div>
                <div style="font-size: 12px;">Get your token from https://are.na/settings/applications</div>
            </div>
            <div id="status" style="margin-top: 10px; font-size: 12px;">Loading...</div>
        </div>
        <div id="image-grid" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px;"></div>
    `;

    document.body.appendChild(overlay);

    const statusEl = overlay.querySelector('#status');
    const gridEl = overlay.querySelector('#image-grid');
    const tokenInput = overlay.querySelector('#arena-token');
    const channelInput = overlay.querySelector('#arena-channel');

    // Ensure inputs are fully editable
    tokenInput.readOnly = false;
    channelInput.readOnly = false;
    tokenInput.disabled = false;
    channelInput.disabled = false;

    // Save config to localStorage on change
    tokenInput.addEventListener('input', () => localStorage.setItem('arenaToken', tokenInput.value));
    channelInput.addEventListener('input', () => localStorage.setItem('arenaChannel', channelInput.value));

    // Add click handler to ensure focus works
    tokenInput.addEventListener('click', (e) => {
        e.stopPropagation();
        tokenInput.focus();
    });
    channelInput.addEventListener('click', (e) => {
        e.stopPropagation();
        channelInput.focus();
    });

    // Close button
    overlay.querySelector('#close-overlay').onclick = () => overlay.remove();

    // Function to add image to Are.na
    async function addToArena(imageUrl, filename, button) {
        const token = tokenInput.value.trim();
        const channel = channelInput.value.trim();

        if (!token || !channel) {
            alert('Please configure your Are.na token and channel slug first');
            return;
        }

        button.disabled = true;
        button.textContent = 'Adding...';

        try {
            const description = `${filename}\nFrom: ${paperTitle || 'arXiv paper'}\n${htmlUrl}`;

            const response = await fetch(`https://api.are.na/v2/channels/${channel}/blocks`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    source: imageUrl,
                    description: description
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || `HTTP ${response.status}`);
            }

            button.textContent = 'Added ✓';
            setTimeout(() => {
                button.disabled = false;
                button.textContent = 'Add to Are.na';
            }, 2000);

        } catch (error) {
            console.error('Error adding to Are.na:', error);
            alert(`Failed to add to Are.na: ${error.message}`);
            button.disabled = false;
            button.textContent = 'Add to Are.na';
        }
    }

    try {
        // Try multiple CORS proxies
        const proxies = [
            `https://api.codetabs.com/v1/proxy?quest=${encodeURIComponent(htmlUrl)}`,
            `https://corsproxy.io/?${encodeURIComponent(htmlUrl)}`,
            `https://api.allorigins.win/raw?url=${encodeURIComponent(htmlUrl)}`
        ];

        let html = null;

        for (let i = 0; i < proxies.length; i++) {
            try {
                statusEl.textContent = `Fetching images... (proxy ${i + 1}/${proxies.length})`;
                const response = await fetch(proxies[i], { signal: AbortSignal.timeout(10000) });

                if (!response.ok) throw new Error(`HTTP ${response.status}`);

                html = await response.text();
                break;
            } catch (err) {
                console.warn(`Proxy ${i + 1} failed:`, err.message);
            }
        }

        if (!html) {
            throw new Error('All proxies failed');
        }

        statusEl.textContent = 'Parsing images...';

        // Parse HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');

        // Extract paper title
        const titleEl = doc.querySelector('title') || doc.querySelector('h1.ltx_title');
        paperTitle = titleEl ? titleEl.textContent.trim() : '';

        const images = doc.querySelectorAll('img');

        const imageData = [];
        const baseOrigin = 'https://arxiv.org';
        const basePath = `/html/${paperId}`;

        images.forEach((img, index) => {
            let src = img.getAttribute('src');
            if (!src) return;

            // Convert relative URLs to absolute
            if (src.startsWith('/')) {
                src = baseOrigin + src;
            } else if (!src.startsWith('http')) {
                src = baseOrigin + basePath + '/' + src;
            }

            // Skip tiny images
            const width = img.width || img.naturalWidth || 0;
            const height = img.height || img.naturalHeight || 0;
            if (width < 50 && height < 50 && (width > 0 || height > 0)) {
                return;
            }

            const filename = src.split('/').pop().split('?')[0] || `image-${index + 1}`;
            imageData.push({ src, filename });
        });

        if (imageData.length === 0) {
            statusEl.textContent = 'No images found';
            return;
        }

        statusEl.textContent = `Found ${imageData.length} image${imageData.length !== 1 ? 's' : ''}`;

        // Display images
        imageData.forEach(img => {
            const card = document.createElement('div');
            card.style.cssText = 'border: 2px solid black;';

            card.innerHTML = `
                <div style="width: 100%; height: 250px; overflow: hidden; border-bottom: 2px solid black; display: flex; align-items: center; justify-content: center;">
                    <img src="${img.src}" style="max-width: 100%; max-height: 100%; object-fit: contain;" loading="lazy">
                </div>
                <div style="padding: 10px;">
                    <div style="font-size: 12px; word-break: break-all; margin-bottom: 10px;">${img.filename}</div>
                    <div class="image-actions" style="display: flex; gap: 0;"></div>
                </div>
            `;

            // Add Are.na button
            const arenaBtn = document.createElement('button');
            arenaBtn.textContent = 'Add to Are.na';
            arenaBtn.style.cssText = 'flex: 1; padding: 8px; text-align: center; background: black; color: white; border: 2px solid black; font-size: 12px; cursor: pointer; font-family: monospace;';
            arenaBtn.addEventListener('click', () => addToArena(img.src, img.filename, arenaBtn));

            card.querySelector('.image-actions').appendChild(arenaBtn);
            gridEl.appendChild(card);
        });

    } catch (error) {
        statusEl.textContent = `Error: ${error.message}`;
    }
})();
