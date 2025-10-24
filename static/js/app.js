  
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
        
        // DOM Elements
        const pinterestUrl = document.getElementById('pinterestUrl');
        const downloadBtn = document.getElementById('downloadBtn');
        const loader = document.getElementById('loader');

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

        document.getElementById('downloadVideoBtn').onclick = function(e) {
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
        };

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
