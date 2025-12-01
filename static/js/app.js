
// Mobile menu toggle functionality
document.getElementById('mobileMenuBtn').addEventListener('click', function () {
    document.getElementById('navMenu').classList.toggle('active');
});

// Language dropdown functionality
const languageDropdown = document.querySelector('.language-dropdown');
const languageTrigger = document.querySelector('.language-trigger');
const languageMenu = document.querySelector('.language-menu');

if (languageDropdown && languageTrigger && languageMenu) {
    const languageForm = document.querySelector('.language-form');
    const nextInput = languageForm ? languageForm.querySelector('input[name="next"]') : null;

    const closeMenu = () => {
        languageDropdown.classList.remove('open');
        languageTrigger.setAttribute('aria-expanded', 'false');
        languageMenu.setAttribute('aria-hidden', 'true');
        languageMenu.hidden = true;
    };

    const openMenu = () => {
        languageDropdown.classList.add('open');
        languageTrigger.setAttribute('aria-expanded', 'true');
        languageMenu.setAttribute('aria-hidden', 'false');
        languageMenu.hidden = false;
    };

    const toggleMenu = () => {
        if (languageDropdown.classList.contains('open')) {
            closeMenu();
        } else {
            openMenu();
        }
    };

    languageTrigger.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopPropagation();
        toggleMenu();
    });

    languageTrigger.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowDown' || event.key === 'Enter' || event.key === ' ') {
            event.preventDefault();
            openMenu();
            const firstOption = languageMenu.querySelector('button');
            if (firstOption) {
                firstOption.focus();
            }
        }
    });

    languageMenu.addEventListener('click', (event) => {
        const target = event.target.closest('button.language-option');
        if (!target) {
            return;
        }
        const targetUrl = target.getAttribute('data-language-url');
        if (nextInput && targetUrl) {
            nextInput.value = targetUrl;
        }
        closeMenu();
    });

    languageMenu.addEventListener('keydown', (event) => {
        const options = Array.from(languageMenu.querySelectorAll('button'));
        const currentIndex = options.indexOf(document.activeElement);

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                options[(currentIndex + 1) % options.length].focus();
                break;
            case 'ArrowUp':
                event.preventDefault();
                options[(currentIndex - 1 + options.length) % options.length].focus();
                break;
            case 'Escape':
                closeMenu();
                languageTrigger.focus();
                break;
            case 'Tab':
                closeMenu();
                break;
            case 'Enter':
            case ' ': {
                const targetUrl = document.activeElement.getAttribute('data-language-url');
                if (nextInput && targetUrl) {
                    nextInput.value = targetUrl;
                }
                break;
            }
            default:
                break;
        }
    });

    document.addEventListener('click', (event) => {
        if (!languageDropdown.contains(event.target)) {
            closeMenu();
        }
    });

    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            closeMenu();
        }
    });

    window.addEventListener('resize', closeMenu);
}

// video download script
const pinterestUrl = document.getElementById('pinterestUrl');
const downloadBtn = document.getElementById('downloadBtn');
const loader = document.getElementById('loader');
if (pinterestUrl && downloadBtn) {
    downloadBtn.addEventListener('click', function() {
        const url = pinterestUrl.value.trim();
        console.log("User entered URL:", url);
        if (!url) {
            console.log("No URL entered");
            showToast('Please enter a Pinterest URL','error');
            return;
        }
        
        if (!isValidPinterestUrl(url)) {
            console.log("Invalid URL format");
            showToast('Please enter a valid Pinterest URL. Example: https://www.pinterest.com/pin/1234567890/', 'error');
            return;
        }
        
        loader.style.display = 'block';
        const downloadSection = document.getElementById('downloadSection');
        fetch('/pin/download', {  // URL to your download endpoint
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken') // Include CSRF token
            },
            body: JSON.stringify({'url': pinterestUrl.value}) // Send any necessary data
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                loader.style.display = 'none';
                showToast(data.error, 'error');
                return;
            }
            var video = document.getElementById('videoPreview');
            var source = document.createElement('source');
            source.setAttribute('src', data.video_url);
            source.setAttribute('type', 'video/mp4');        
            video.appendChild(source);
            loader.style.display = 'none';
            downloadSection.setAttribute('style', 'display: none;');
            video.setAttribute('style', 'display: block;');
            video.load();
            video.play();
            document.getElementById('downloadBtnSection').style.display = 'block';
        })
        .catch(error => console.error('Error:', error));
    });
    document.getElementById('downloadVideoBtn').addEventListener('click', function(e) {
        window.open('https://otieu.com/4/10211127', '_blank', 'noopener');

        loader.style.display = 'block';
        var video = document.getElementById('videoPreview');
        var hiddenInput = document.getElementById('hiddenVideoUrl');
        if (video && video.currentSrc) {
            hiddenInput.value = video.currentSrc;
        } else {
            e.preventDefault();
            showToast('No video loaded to download.', 'error');
        }
        loader.style.display = 'none';
    });
}

// image download script
const pinterestImageUrl = document.getElementById('pinterestImageUrl');
const downloadImageButton = document.getElementById('downloadImageButton');

if (pinterestImageUrl && downloadImageButton) {
    downloadImageButton.addEventListener('click', function() {
        const url = pinterestImageUrl.value.trim();
        console.log("User entered URL:", url);
        if (!url) {
            console.log("No URL entered");
            showToast('Please enter a Pinterest URL','error');
            return;
        }
        
        if (!isValidPinterestUrl(url)) {
            console.log("Invalid URL format");
            showToast('Please enter a valid Pinterest URL. Example: https://www.pinterest.com/pin/1234567890/', 'error');
            return;
        }
        
        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        const downloadSection = document.getElementById('downloadSection');
        fetch('/pin/downloadPinterestImage', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({'url': pinterestImageUrl.value})
        })
        .then(response => response.json())
        .then(data => {
            loader.style.display = 'none';
            if (data.image_url) {
                const imagePreview = document.getElementById('imagePreview');
                if (imagePreview) {
                    imagePreview.src = data.image_url;
                    imagePreview.style.display = 'block';
                    downloadSection.setAttribute('style', 'display: none;');
                    document.getElementById('downloadImageBtnSection').style.display = 'block';
                    document.getElementById('imagePreviewUrl').href = data.image_url;
                    document.getElementById('imagePreviewUrl').target = '_blank';
                    const hiddenImageUrl = document.getElementById('hiddenImageUrl');
                    if (hiddenImageUrl) {
                        hiddenImageUrl.value = data.image_url;
                    }
                } else {
                    showToast('Image preview element not found', 'error');
                }
            } else {
                showToast('Failed to extract image URL from Pinterest', 'error');
            }
        })
        .catch(error => {
            loader.style.display = 'none';
            console.error('Error:', error);
            showToast('An error occurred while processing your request', 'error');
        });
    });

    document.getElementById('downloadImageFileBtn').onclick = function(e) {
        window.open('https://otieu.com/4/10211127', '_blank', 'noopener');

        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        const imagePreview = document.getElementById('imagePreview');
        const hiddenImageUrl = document.getElementById('hiddenImageUrl');
        if (imagePreview && imagePreview.src) {
            hiddenImageUrl.value = imagePreview.src;
        } else {
            e.preventDefault();
            showToast('No image loaded to download.', 'error');
        }
        loader.style.display = 'none';
    };
}
   
// gif download script
const pinterestGifUrl = document.getElementById('pinterestGifUrl');
const downloadGifButton = document.getElementById('downloadGifButton');

if (pinterestGifUrl && downloadGifButton) {
    downloadGifButton.addEventListener('click', function() {
        const url = pinterestGifUrl.value.trim();
        console.log("User entered URL:", url);
        if (!url) {
            console.log("No URL entered");
            showToast('Please enter a Pinterest URL','error');
            return;
        }
        
        if (!isValidPinterestUrl(url)) {
            console.log("Invalid URL format");
            showToast('Please enter a valid Pinterest URL. Example: https://www.pinterest.com/pin/1234567890/', 'error');
            return;
        }
        
        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        const downloadSection = document.getElementById('downloadSection');
        fetch('/pin/downloadPinterestGif', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({'url': pinterestGifUrl.value})
        })
        .then(response => {
            // Always return the parsed body so downstream handlers get data
            return response.json().catch(() => {
                throw new Error('Invalid JSON response from server');
            });
        })
        .then(data => {
            console.log("data:", data);
            loader.style.display = 'none';
            if (data.gif_url) {
                const gifPreviewVideo = document.getElementById('gifPreviewVideo');
                const gifPreviewImage = document.getElementById('gifPreviewImage');
                const urlLower = data.gif_url.toLowerCase();
                const isVideo = urlLower.endsWith('.mp4') || urlLower.endsWith('.webm');

                if (isVideo && gifPreviewVideo) {
                    gifPreviewVideo.src = data.gif_url;
                    gifPreviewVideo.style.display = 'block';
                    if (gifPreviewImage) {
                        gifPreviewImage.style.display = 'none';
                        gifPreviewImage.src = '';
                    }
                } else if (gifPreviewImage) {
                    gifPreviewImage.src = data.gif_url;
                    gifPreviewImage.style.display = 'block';
                    if (gifPreviewVideo) {
                        gifPreviewVideo.pause();
                        gifPreviewVideo.removeAttribute('src');
                        gifPreviewVideo.load();
                        gifPreviewVideo.style.display = 'none';
                    }
                }

                if (gifPreviewVideo || gifPreviewImage) {
                    downloadSection.setAttribute('style', 'display: none;');
                    document.getElementById('downloadGifBtnSection').style.display = 'block';
                    const hiddenGifUrl = document.getElementById('hiddenGifUrl');
                    if (hiddenGifUrl) {
                        hiddenGifUrl.value = data.gif_url;
                    }
                } else {
                    showToast('GIF preview element not found', 'error');
                }
            } else {
                showToast(data.error || 'Failed to extract GIF URL from Pinterest', 'error');
            }
        })
        .catch(error => {
            loader.style.display = 'none';
            console.error('Error:', error);
            showToast('An error occurred while processing your request', 'error');
        });
    });

    document.getElementById('downloadGifFileBtn').onclick = function(e) {
        window.open('https://otieu.com/4/10211127', '_blank', 'noopener');

        const loader = document.getElementById('loader');
        loader.style.display = 'block';
        const hiddenGifUrl = document.getElementById('hiddenGifUrl');
        const gifPreviewVideo = document.getElementById('gifPreviewVideo');
        const gifPreviewImage = document.getElementById('gifPreviewImage');
        const activeSrc = (gifPreviewVideo && gifPreviewVideo.style.display !== 'none' && gifPreviewVideo.src)
            || (gifPreviewImage && gifPreviewImage.style.display !== 'none' && gifPreviewImage.src);

        if (activeSrc) {
            hiddenGifUrl.value = activeSrc;
        } else {
            e.preventDefault();
            showToast('No GIF loaded to download.', 'error');
        }
        loader.style.display = 'none';
    };
}

// Reload GIF downloader page on "Download More Gifs" click
(() => {
    const reloadBtn = document.getElementById('downloadMoreGifBtn');
    if (!reloadBtn) return;
    reloadBtn.addEventListener('click', (event) => {
        event.preventDefault();
        window.location.reload();
    });
})();

// Reload image downloader page on "Download More Images" click
(() => {
    const reloadBtn = document.getElementById('downloadMoreImageBtn');
    if (!reloadBtn) return;
    reloadBtn.addEventListener('click', (event) => {
        event.preventDefault();
        window.location.reload();
    });
})();

// Reload profile downloader page on "Download More Pictures" click
(() => {
    const reloadBtn = document.getElementById('downloadMoreProfileBtn');
    if (!reloadBtn) return;
    reloadBtn.addEventListener('click', (event) => {
        event.preventDefault();
        window.location.reload();
    });
})();

// Reload video downloader page on "Download More Videos" click
(() => {
    const reloadBtn = document.getElementById('downloadMoreBtn');
    if (!reloadBtn) return;
    reloadBtn.addEventListener('click', (event) => {
        event.preventDefault();
        window.location.reload();
    });
})();


// Function to get CSRF token from cookies (required for Django POST requests)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Validate Pinterest URL
function isValidPinterestUrl(url) {
    const pattern = /^https?:\/\/(?:www\.)?pinterest\.(com|it|fr|de|es|co\.uk|ca|com\.au|co\.nz|pt|nl|co\.in|co\.jp|co\.kr|ru|com\.mx|co\.id|com\.br|com\.tr)\/pin\/[0-9]+\/?/i;
    return pattern.test(url) || /^https?:\/\/pin\.it\/[a-zA-Z0-9]+/i.test(url);
}

// Show toast notification
function showToast(message, type) {
    const toastContainer = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.classList.add('toast', type);
    toast.textContent = message;

    toastContainer.appendChild(toast);

    // Show the toast with a slight delay for animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);

    // Remove the toast after 3 seconds
    setTimeout(() => {
        toast.classList.remove('show');
        // Wait for fade-out animation to complete before removing from DOM
        setTimeout(() => {
            toast.remove();
        }, 500); // Should match CSS transition duration
    }, 3000);
}
