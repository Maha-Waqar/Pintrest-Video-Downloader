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

def _download_image_file(image_url, filename):
    try:
        response = requests.get(image_url, stream=True, headers={'User-Agent': 'Mozilla/5.0'})
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
        print(f"Error downloading image: {e}")
        return None

@csrf_exempt
def download_image(request):
    if request.method == 'POST':
        image_url = request.POST.get('image_url')
        filename = datetime.now().strftime('%d_%m_%H_%M_%S_') + '.jpg'
        if not image_url:
            return HttpResponse('No image URL provided', status=400)
        filepath = _download_image_file(image_url, filename)
        if not filepath:
            return HttpResponse('Failed to download image', status=500)
        with open(filepath, 'rb') as f:
            response = HttpResponse(f.read(), content_type='image/jpeg')
            response['Content-Disposition'] = f'attachment; filename="{smart_str(filename)}"'
            return response
    return HttpResponse('Invalid request method', status=405)

def extract_image_url_from_soup(soup):
    """
    Extract image URL from Pinterest pin page HTML.
    Looks for og:image meta tag, img tags, and script-embedded URLs.
    Returns the first found image URL, or None if not found.
    """
    meta = soup.find('meta', property='og:image')
    if meta and meta.get('content'):
        src = meta['content']
        if src and not src.startswith('blob:'):
            return src
    
    img_tags = soup.find_all('img')
    for img in img_tags:
        src = img.get('src')
        if src and ('pinimg' in src or 'pinterest' in src) and not src.startswith('blob:'):
            if src.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
                return src
    
    scripts = soup.find_all('script')
    for script in scripts:
        if script.string:
            urls = re.findall(r'(https://[^\s"\']+\.pinimg\.com/[^\s"\']+\.(?:jpg|jpeg|png|gif|webp))', script.string)
            if urls:
                return urls[0]
    
    return None

def is_valid_image_url(url):
    """Check if the given URL is a valid image URL."""
    try:
        resp = requests.head(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=4, allow_redirects=True)
        if resp.status_code == 200:
            content_type = resp.headers.get('content-type', '').lower()
            return 'image' in content_type
        return False
    except Exception:
        return False

def get_image_url(page_url):
    """
    Attempts to extract a direct image URL from a Pinterest pin page.
    1. Tries fast extraction using requests + BeautifulSoup.
    2. If not found, falls back to Selenium (headless Chrome) for dynamic content.
    Returns a valid image URL or None if not possible.
    """
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        resp = requests.get(page_url, headers=headers, timeout=8)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            url = extract_image_url_from_soup(soup)
            if url and is_valid_image_url(url):
                return url
    except Exception:
        pass
    
    try:
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-dev-shm-usage')
   
        # Ensure correct Chrome binary path
        options.binary_location = '/usr/bin/google-chrome'

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(page_url)
        time.sleep(0.5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        url = extract_image_url_from_soup(soup)
        driver.quit()
        if url and is_valid_image_url(url):
            return url
        return None
    except Exception:
        return None

def download_pinterest_image(request):
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid or empty JSON body.'}, status=400)
    page_url = data.get('url')
    image_url = get_image_url(page_url)
    data = {'image_url': image_url}
    return JsonResponse(data)
