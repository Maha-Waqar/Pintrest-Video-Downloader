from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import requests, json
from bs4 import BeautifulSoup
import os, re
import tempfile
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.utils.encoding import smart_str
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from django_ratelimit.decorators import ratelimit
import html
from urllib.parse import urlparse

MEDIA_EXTENSIONS = ('.gif', '.mp4', '.webm', '.m3u8')
PINIMG_MEDIA_RE = re.compile(
    r'(https?://[^\s"\'\\]+?pinimg\.com[^\s"\'\\]+?\.(?:gif|mp4|webm|m3u8)(?:\?[^\s"\'\\]*)?)',
    re.IGNORECASE,
)

REQUEST_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0 Safari/537.36',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}


def _url_has_extension(url, extensions=MEDIA_EXTENSIONS):
    if not url:
        return False
    try:
        path = urlparse(url).path.lower()
    except Exception:
        return False
    return any(path.endswith(ext) for ext in extensions)


def _clean_pinimg_url(url):
    if not url:
        return url
    cleaned = html.unescape(
        url.replace("\\u002F", "/")
        .replace("\\/", "/")
        .replace("\\u0026", "&")
        .replace("\u0026", "&")
    )
    if cleaned.startswith("//"):
        cleaned = f"https:{cleaned}"
    return cleaned


def _extract_media_urls_from_text(text):
    if not text:
        return []
    cleaned_text = text.replace("\\u002F", "/").replace("\\u0026", "&")
    return PINIMG_MEDIA_RE.findall(cleaned_text)


def _walk_json_for_urls(node, found):
    if isinstance(node, dict):
        for value in node.values():
            _walk_json_for_urls(value, found)
    elif isinstance(node, list):
        for item in node:
            _walk_json_for_urls(item, found)
    elif isinstance(node, str):
        candidate = _clean_pinimg_url(node)
        if 'pinimg.com' in candidate and _url_has_extension(candidate):
            found.append(candidate)


def _probe_url_ok(url):
    try:
        resp = requests.head(url, headers=REQUEST_HEADERS, timeout=4, allow_redirects=True)
        return 200 <= resp.status_code < 400
    except Exception:
        return False


def _select_best_media_url(urls):
    if not urls:
        return None
    seen = set()
    ordered = []
    for url in urls:
        if not url or url.startswith('blob:'):
            continue
        cleaned = _clean_pinimg_url(url)
        if cleaned not in seen:
            seen.add(cleaned)
            ordered.append(cleaned)

    preferred_exts = ('.mp4', '.gif', '.webm', '.m3u8')
    for ext in preferred_exts:
        for url in ordered:
            if _url_has_extension(url, (ext,)):
                if ext == '.m3u8':
                    mp4_candidates = [
                        url.replace('hls', '720p').replace('m3u8', 'mp4'),
                        url.replace('/master.m3u8', '/720p.mp4'),
                        url.replace('/playlist.m3u8', '/720p.mp4'),
                    ]
                    for candidate in mp4_candidates:
                        if candidate and _probe_url_ok(candidate):
                            return candidate
                    return url
                return url
    return ordered[0] if ordered else None


def _infer_filename_and_mime(gif_url):
    parsed_path = ''
    try:
        parsed_path = urlparse(gif_url).path.lower()
    except Exception:
        parsed_path = gif_url or ''
    if parsed_path.endswith('.mp4'):
        return '.mp4', 'video/mp4'
    if parsed_path.endswith('.webm'):
        return '.webm', 'video/webm'
    return '.gif', 'image/gif'


def _download_gif_file(gif_url, filename):
    try:
        response = requests.get(gif_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
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
        print(f"Error downloading gif: {e}")
        return None

@csrf_exempt
def download_gif(request):
    if request.method == 'POST':
        gif_url = request.POST.get('gif_url')
        if not gif_url:
            return HttpResponse('No GIF URL provided', status=400)
        ext, content_type = _infer_filename_and_mime(gif_url)
        filename = datetime.now().strftime('%d_%m_%H_%M_%S_') + ext
        filepath = _download_gif_file(gif_url, filename)
        if not filepath:
            return HttpResponse('Failed to download GIF', status=500)
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
            return response
    return HttpResponse('Invalid request method', status=405)

def extract_gif_url_from_soup(soup, page_html: str = ""):
    """
    Extract GIF URL from Pinterest pin page HTML.
    Looks for og:image, .gif URLs, and video tags that might be animated.
    Returns the first found GIF/animated URL, or None if not found.
    """
    candidates = []

    def _add(url):
        if url:
            candidates.append(url)

    for prop in ('og:video', 'og:video:secure_url', 'twitter:player:stream'):
        meta_video = soup.find('meta', property=prop) or soup.find('meta', attrs={'name': prop})
        if meta_video and meta_video.get('content'):
            _add(meta_video['content'])

    meta = soup.find('meta', property='og:image')
    if meta and meta.get('content'):
        src = meta['content']
        if _url_has_extension(src):
            _add(src)

    for img in soup.find_all('img'):
        src = img.get('src')
        if src and 'pinimg' in src and _url_has_extension(src):
            _add(src)
        srcset = img.get('srcset')
        if srcset:
            for candidate in srcset.split(','):
                candidate_url = candidate.strip().split(' ')[0]
                if candidate_url and 'pinimg' in candidate_url and _url_has_extension(candidate_url):
                    _add(candidate_url)

    for video in soup.find_all('video'):
        src = video.get('src')
        if src and _url_has_extension(src):
            _add(src)
        for source in video.find_all('source', src=True):
            if _url_has_extension(source['src']):
                _add(source['src'])

    for link in soup.find_all('link', href=True):
        href = link['href']
        if 'pinimg' in href and _url_has_extension(href):
            _add(href)

    scripts = soup.find_all('script')
    for script in scripts:
        content = script.string or script.get_text() or ""
        if not content:
            continue

        if script.get('type') == 'application/json' or script.get('id') == '__PWS_DATA__' or content.strip().startswith('{'):
            try:
                json_blob = json.loads(content)
                json_urls = []
                _walk_json_for_urls(json_blob, json_urls)
                for url in json_urls:
                    _add(url)
            except Exception:
                pass

        for url in _extract_media_urls_from_text(content):
            _add(url)

    if page_html:
        for url in _extract_media_urls_from_text(page_html):
            _add(url)

    return _select_best_media_url(candidates)

def is_valid_gif_url(url):
    """Check if the given URL is a valid GIF/animated file URL."""
    try:
        resp = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4, allow_redirects=True)
        if resp.status_code == 200:
            content_type = resp.headers.get('content-type', '').lower()
            return 'image' in content_type or 'video' in content_type
        return False
    except Exception:
        return False

def get_gif_url(page_url):
    """
    Attempts to extract a GIF URL from a Pinterest pin page.
    1. Tries fast extraction using requests + BeautifulSoup.
    2. If not found, falls back to Selenium (headless Chrome) for dynamic content.
    Returns a valid GIF URL or None if not possible.
    """
    try:
        resp = requests.get(page_url, headers=REQUEST_HEADERS, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            url = extract_gif_url_from_soup(soup, resp.text)
            print('url', url)
            print("Extracted URL:", url);
            # Return the first extracted URL even if the HEAD validation fails,
            # since Pinterest often blocks HEAD requests.
            if url:
                return url
    except Exception:
        pass
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(page_url)
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        url = extract_gif_url_from_soup(soup, driver.page_source)
        driver.quit()
        # Same here: accept the extracted URL without HEAD validation to avoid
        # false negatives from Pinterest blocking HEAD requests.
        if url:
            return url
        return None
    except Exception:
        return None

def download_pinterest_gif(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid or empty JSON body.'}, status=400)
    page_url = data.get('url')
    gif_url = get_gif_url(page_url)

    if not gif_url:
        return JsonResponse(
            {"gif_url": None, "error": "Could not extract a GIF from this link. Please check the URL or try again."},
            status=200,
        )

    return JsonResponse({"gif_url": gif_url})
