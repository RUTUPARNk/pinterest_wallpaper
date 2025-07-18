
from flask import Flask, send_file, jsonify, request
import requests
import xml.etree.ElementTree as ET
import logging
import time
import json
import os

app = Flask(__name__)

# Set up logging
logging.basicConfig(
    filename='server.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Cache file for storing last successful image list
CACHE_FILE = 'image_cache.json'

# User-Agent list for rotation
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
]

# Proxy for fallback
PROXY_URL = 'https://cors-anywhere.herokuapp.com/'

def load_cached_images():
    """Load cached image URLs from file."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        logging.error(f"Error loading cache: {e}")
        return []

def save_cached_images(image_urls):
    """Save image URLs to cache file."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(image_urls, f)
        logging.info("Saved images to cache")
    except Exception as e:
        logging.error(f"Error saving cache: {e}")

@app.route('/')
def index():
    return send_file('aim/slideshow.html')  # Serve from aim subdirectory

@app.route('/images')
def get_images():
    try:
        # Get offset for pagination
        offset = int(request.args.get('offset', 0))
        rss_url = 'https://in.pinterest.com/rockkulkarni/aim.rss'
        max_retries = 5
        image_urls = []

        # Try direct fetch first
        for attempt in range(max_retries):
            try:
                headers = {'User-Agent': USER_AGENTS[attempt % len(USER_AGENTS)]}
                response = requests.get(rss_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    break
                logging.warning(f"Direct attempt {attempt + 1} failed: Status {response.status_code}")
                time.sleep(3)
            except requests.RequestException as e:
                logging.warning(f"Direct attempt {attempt + 1} failed: {e}")
                time.sleep(3)
        else:
            # Fallback to proxy
            logging.info("Falling back to proxy for RSS fetch")
            try:
                response = requests.get(PROXY_URL + rss_url, headers={'User-Agent': USER_AGENTS[0]}, timeout=10)
                if response.status_code != 200:
                    logging.error(f"Proxy fetch failed: Status {response.status_code}")
                    return jsonify(load_cached_images()[offset:offset+10]), 500
            except requests.RequestException as e:
                logging.error(f"Proxy fetch failed: {e}")
                return jsonify(load_cached_images()[offset:offset+10]), 500

        # Parse RSS XML
        xml_doc = ET.fromstring(response.text)
        items = xml_doc.findall('.//item')
        image_urls = []

        # Extract image URLs from RSS
        for item in items:
            description = item.find('description').text or ''
            match = None
            if description:
                start = description.find('src="') + 5
                end = description.find('"', start)
                if start != -1 and end != -1:
                    match = description[start:end]
            if match and 'pinimg.com' in match:
                # Update the replacement line:
                high_res_url = match.replace('/236x/', '/originals/').replace('/564x/', '/originals/').replace('/474x/', '/originals/')
                image_urls.append(high_res_url)

        if image_urls:
            save_cached_images(image_urls)
            logging.info(f"Fetched {len(image_urls)} images from RSS feed")
        else:
            logging.warning("No images found in RSS feed")

        return jsonify(image_urls[offset:offset+10])  # Return 10 images starting at offset
    except Exception as e:
        logging.error(f"Error fetching images: {e}")
        cached_images = load_cached_images()
        if cached_images:
            return jsonify(cached_images[offset:offset+10])
        return jsonify([]), 500

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port=5000)
