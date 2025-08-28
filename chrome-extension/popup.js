document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('videoForm');
    const serverUrlInput = document.getElementById('serverUrl');
    const imageFileInput = document.getElementById('imageFile');
    const audioFileInput = document.getElementById('audioFile');
    const resolutionSelect = document.getElementById('resolution');
    const createBtn = document.getElementById('createBtn');
    const statusDiv = document.getElementById('status');

    // Load saved server URL
    chrome.storage.sync.get(['serverUrl'], function(result) {
        if (result.serverUrl) {
            serverUrlInput.value = result.serverUrl;
        }
    });

    // Save server URL when changed
    serverUrlInput.addEventListener('change', function() {
        chrome.storage.sync.set({ serverUrl: serverUrlInput.value });
    });

    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = `status ${type}`;
        statusDiv.classList.remove('hidden');
    }

    function hideStatus() {
        statusDiv.classList.add('hidden');
    }

    function setLoading(loading) {
        createBtn.disabled = loading;
        createBtn.textContent = loading ? '⏳ Processing...' : '🚀 Create Video';
    }

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const imageFile = imageFileInput.files[0];
        const audioFile = audioFileInput.files[0];
        const resolution = resolutionSelect.value;
        const serverUrl = serverUrlInput.value.trim();

        if (!imageFile || !audioFile) {
            showStatus('Please select both image and audio files', 'error');
            return;
        }

        if (!serverUrl) {
            showStatus('Please enter a valid server URL', 'error');
            return;
        }

        try {
            setLoading(true);
            showStatus('Creating video...', 'processing');

            // Check if server is running
            const healthResponse = await fetch(`${serverUrl}/_health`);
            if (!healthResponse.ok) {
                throw new Error('Server is not responding. Please make sure the local server is running.');
            }

            // Prepare form data
            const formData = new FormData();
            formData.append('image', imageFile);
            formData.append('audio', audioFile);
            formData.append('resolution', resolution);

            // Send request to local server
            const response = await fetch(`${serverUrl}/`, {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                // Check if response is a redirect (which means we got a download URL)
                if (response.redirected) {
                    showStatus('Video created successfully!', 'success');
                    
                    // Create download link
                    const downloadLink = document.createElement('a');
                    downloadLink.href = response.url;
                    downloadLink.textContent = '📥 Download Video';
                    downloadLink.className = 'download-link';
                    downloadLink.target = '_blank';
                    
                    statusDiv.appendChild(document.createElement('br'));
                    statusDiv.appendChild(downloadLink);
                } else {
                    // For local mode, we might get a JSON response with download URL
                    const result = await response.json();
                    if (result.downloadUrl) {
                        showStatus('Video created successfully!', 'success');
                        
                        const downloadLink = document.createElement('a');
                        downloadLink.href = `${serverUrl}${result.downloadUrl}`;
                        downloadLink.textContent = '📥 Download Video';
                        downloadLink.className = 'download-link';
                        downloadLink.target = '_blank';
                        
                        statusDiv.appendChild(document.createElement('br'));
                        statusDiv.appendChild(downloadLink);
                    } else {
                        showStatus('Video created but no download link received', 'error');
                    }
                }
            } else {
                const errorText = await response.text();
                throw new Error(errorText || 'Failed to create video');
            }
        } catch (error) {
            console.error('Error creating video:', error);
            showStatus(`Error: ${error.message}`, 'error');
        } finally {
            setLoading(false);
        }
    });

    // Test server connection when URL changes
    serverUrlInput.addEventListener('blur', async function() {
        const serverUrl = serverUrlInput.value.trim();
        if (!serverUrl) return;

        try {
            const response = await fetch(`${serverUrl}/_health`, { method: 'GET' });
            if (response.ok) {
                serverUrlInput.style.borderColor = '#28a745';
            } else {
                serverUrlInput.style.borderColor = '#dc3545';
            }
        } catch (error) {
            serverUrlInput.style.borderColor = '#dc3545';
        }
    });
});