import json
import os
import re
import tempfile
import time
from datetime import datetime

from bs4 import BeautifulSoup
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django_ratelimit.decorators import ratelimit
from django.utils.encoding import smart_str
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from pincatch.proxy_pool import (
    add_proxy_to_chrome_options,
    mark_proxy_failure,
    mark_proxy_success,
    proxy_request,
)

def index(request):
    return render(request, 'index.html', { 'video_url': '' })

# helper function to download video
def _download_video_file(video_url, filename):
    try:
        response = proxy_request("get", video_url, stream=True, timeout=10)
        if response.status_code == 200:
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, filename)
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return filepath
        else:
            return None
    except Exception as e:
        print(f"Error downloading video: {e}")
        return None

# function to handle video download request
@csrf_exempt
def download_video(request):
    if request.method == 'POST':
        video_url = request.POST.get('video_url')
        filename = datetime.now().strftime('%d_%m_%H_%M_%S_') + '.mp4'
        if not video_url:
            return HttpResponse('No video URL provided', status=400)
        filepath = _download_video_file(video_url, filename)
        if not filepath:
            return HttpResponse('Failed to download video', status=500)
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='video/mp4')
            response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
            return response
    return HttpResponse('Invalid request method', status=405)

# --- Pinterest Video Extraction Utilities ---

def extract_video_url_from_soup(soup):
    """
    Try to extract a direct video URL from the HTML soup.
    Looks for <video> tags, <source> tags, og:video meta, and script-embedded URLs.
    Returns the first found mp4 or m3u8 URL, or None if not found.
    """
    video_tag = soup.find('video', src=True)
    if video_tag:
        src = video_tag['src']
        if not src.startswith('blob:'):
            return src
    video = soup.find('video')
    if video:
        source = video.find('source', src=True)
        if source:
            src = source['src']
            if not src.startswith('blob:'):
                return src
    meta = soup.find('meta', property='og:video')
    if meta and meta.get('content'):
        src = meta['content']
        if not src.startswith('blob:'):
            return src
    import re
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            urls = re.findall(r'(https://v1\.pinimg\.com/videos/[^"\']+\.(?:mp4|m3u8))', script.string)
            if urls:
                return urls[0]
    return None

def try_convert_m3u8_to_mp4(url):
    if url and url.endswith('.m3u8') and 'hls' in url:
        mp4_url = url.replace('hls', '720p').replace('m3u8', 'mp4')
        try:
            resp = proxy_request("head", mp4_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4, allow_redirects=True)
            if resp.status_code == 200:
                return mp4_url
        except Exception:
            pass
    return None

def get_video_url(page_url):
    """
    Attempts to extract a direct mp4 video URL from a Pinterest pin page.
    1. Tries fast extraction using requests + BeautifulSoup.
    2. If not found, falls back to Selenium (headless Chrome) for dynamic content.
    3. Only returns a valid mp4 URL (never m3u8). Returns None if not possible.
    """
    def is_valid_mp4(url):
        """Checks if the given URL is a valid mp4 file (HTTP 200 and ends with .mp4)."""
        try:
            resp = proxy_request("head", url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4, allow_redirects=True)
            return resp.status_code == 200 and url.endswith('.mp4')
        except Exception:
            return False

    # Fast method: requests + BeautifulSoup
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        resp = proxy_request("get", page_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            url = extract_video_url_from_soup(soup)
            # Try mp4 directly
            if url and url.endswith('.mp4') and is_valid_mp4(url):
                return url
            # Try to convert m3u8 to mp4 using Pinterest's known pattern
            if url and url.endswith('.m3u8') and 'hls' in url:
                mp4_url = url.replace('hls', '720p').replace('m3u8', 'mp4')
                if is_valid_mp4(mp4_url):
                    return mp4_url
    except Exception:
        pass
    # Fallback: Selenium (minimal wait)
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    proxy_used = add_proxy_to_chrome_options(options)
    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(page_url)
        time.sleep(0.5)  # Minimal wait for JS to load dynamic content
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        url = extract_video_url_from_soup(soup)
        if url and url.endswith('.mp4') and is_valid_mp4(url):
            if proxy_used:
                mark_proxy_success(proxy_used)
            return url
        if url and url.endswith('.m3u8') and 'hls' in url:
            mp4_url = url.replace('hls', '720p').replace('m3u8', 'mp4')
            if is_valid_mp4(mp4_url):
                if proxy_used:
                    mark_proxy_success(proxy_used)
                return mp4_url
        return None
    except Exception:
        if proxy_used:
            mark_proxy_failure(proxy_used)
        return None
    finally:
        try:
            if driver:
                driver.quit()
        except Exception:
            pass

def download_pinterest_video(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid or empty JSON body.'}, status=400)

    page_url = data.get('url')
    video_url = get_video_url(page_url)

    if not video_url:
        return JsonResponse(
            {"video_url": None, "error": "Could not extract a video from this link. Please check the URL or try again."},
            status=200,
        )

    lowered = video_url.lower()
    if lowered.endswith(".gif"):
        return JsonResponse(
            {
                "video_url": None,
                "error": "This link points to a GIF. Please use the GIF downloader for this pin.",
            },
            status=200,
        )

    return JsonResponse({'video_url': video_url})

def is_valid_url(url):
    return re.match(r'^https?://(www\.)?pinterest\.com/', url)

def home(request):
    # CSRF protection is enabled by default with csrf_protect
    @csrf_protect
    @ratelimit(key='ip', rate='10/m', block=True)
    def protected_home(request):
        # User-Agent check
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'python' in user_agent.lower() or not user_agent:
            return HttpResponse('Forbidden: Suspicious User-Agent', status=403)
        # Referrer check (optional, can be commented out if not needed)
        referrer = request.META.get('HTTP_REFERER', '')
        if referrer and not referrer.startswith('https://yourdomain.com'):
            return HttpResponse('Forbidden: Invalid Referrer', status=403)
        # Example: Validate input URL if present
        page_url = request.GET.get('url')
        if page_url and not is_valid_url(page_url):
            return HttpResponse('Invalid Pinterest URL', status=400)
        # ...existing logic...
        return render(request, 'index.html', { 'video_url': '' })
    return protected_home(request)
