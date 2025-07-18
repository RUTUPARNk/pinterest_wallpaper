
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import os
import requests
import time
import logging
import signal
import sys

# Configuration
GOOGLE_EMAIL = "your_google_email@gmail.com"  # Replace with your Google account email
GOOGLE_PASSWORD = "your_google_password"  # Replace with your Google account password
BOARD_URL = "https://www.pinterest.com/your_username/your_board"  # Replace with public board URL
DOWNLOAD_FOLDER = "C:/PinterestImages"  # Local folder to store images
UPDATE_INTERVAL = 300  # Update every 5 minutes (in seconds)
MAX_IMAGES = 10  # Maximum images to download per cycle
TRIGGER_FILE = os.path.join(DOWNLOAD_FOLDER, "trigger_scrape.txt")  # File to trigger immediate scrape

# Set up logging
logging.basicConfig(
    filename='scraper.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Ensure download folder exists
if not os.path.exists(DOWNLOAD_FOLDER):
    os.makedirs(DOWNLOAD_FOLDER)
    logging.info(f"Created download folder: {DOWNLOAD_FOLDER}")

def setup_driver():
    """Initialize Selenium WebDriver with headless Chrome."""
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        logging.info("WebDriver initialized successfully")
        return driver
    except WebDriverException as e:
        logging.error(f"Failed to initialize WebDriver: {e}")
        raise

def login_to_pinterest(driver):
    """Log in to Pinterest using Google OAuth."""
    try:
        driver.get("https://www.pinterest.com/login/")
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Continue with Google')]"))
        )
        google_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Continue with Google')]")
        google_button.click()
        logging.info("Clicked 'Continue with Google' button")

        # Switch to Google login window
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(2))
        driver.switch_to.window(driver.window_handles[1])

        # Enter Google email
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "identifierId"))
        )
        email_field = driver.find_element(By.ID, "identifierId")
        email_field.send_keys(GOOGLE_EMAIL)
        driver.find_element(By.ID, "identifierNext").click()
        logging.info("Entered Google email")

        # Enter Google password
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "Passwd"))
        )
        password_field = driver.find_element(By.NAME, "Passwd")
        password_field.send_keys(GOOGLE_PASSWORD)
        driver.find_element(By.ID, "passwordNext").click()
        logging.info("Entered Google password")

        # Switch back to main window
        WebDriverWait(driver, 10).until(EC.number_of_windows_to_be(1))
        driver.switch_to.window(driver.window_handles[0])

        # Wait for Pinterest redirect
        WebDriverWait(driver, 15).until(
            EC.url_contains("pinterest.com")
        )
        logging.info("Successfully logged in to Pinterest via Google")
    except TimeoutException as e:
        logging.error(f"Login failed - Timeout: {e}")
        raise
    except Exception as e:
        logging.error(f"Login failed: {e}")
        raise

def download_image(url, filename):
    """Download an image from a URL to the specified filename."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, stream=True, timeout=10)
        if response.status_code == 200 and 'image' in response.headers.get('content-type', ''):
            with open(filename, 'wb') as f:
                f.write(response.content)
            logging.info(f"Downloaded image: {filename}")
            return True
        else:
            logging.warning(f"Invalid response for {url}: Status {response.status_code}")
            return False
    except Exception as e:
        logging.error(f"Error downloading {url}: {e}")
        return False

def clean_old_images():
    """Remove old images from the download folder, except trigger file."""
    try:
        for file in os.listdir(DOWNLOAD_FOLDER):
            if file == "trigger_scrape.txt":
                continue
            file_path = os.path.join(DOWNLOAD_FOLDER, file)
            if os.path.isfile(file_path):
                os.remove(file_path)
                logging.info(f"Removed old image: {file_path}")
    except Exception as e:
        logging.error(f"Error cleaning old images: {e}")

def scrape_pins():
    """Scrape and download images from a Pinterest board."""
    driver = None
    try:
        driver = setup_driver()
        login_to_pinterest(driver)
        driver.get(BOARD_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "img[src*='pinimg.com']"))
        )

        # Scroll to load more pins
        for _ in range(2):  # Scroll twice for more images
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)

        # Find image elements
        images = driver.find_elements(By.CSS_SELECTOR, "img[src*='pinimg.com']")
        image_urls = [img.get_attribute("src") for img in images if img.get_attribute("src")]

        # Clean old images
        clean_old_images()

        # Download new images
        downloaded = 0
        for i, url in enumerate(image_urls):
            if downloaded >= MAX_IMAGES:
                break
            if url:
                # Convert to high-res URL
                high_res_url = url.replace("/236x/", "/originals/").replace("/564x/", "/originals/")
                filename = os.path.join(DOWNLOAD_FOLDER, f"pin_{i}.jpg")
                if download_image(high_res_url, filename):
                    downloaded += 1

        logging.info(f"Downloaded {downloaded} images")
        return downloaded > 0

    except Exception as e:
        logging.error(f"Scrape failed: {e}")
        return False
    finally:
        if driver:
            driver.quit()
            logging.info("WebDriver closed")

def check_trigger_file():
    """Check if trigger file exists and remove it to trigger immediate scrape."""
    if os.path.exists(TRIGGER_FILE):
        try:
            os.remove(TRIGGER_FILE)
            logging.info("Trigger file detected and removed, initiating immediate scrape")
            return True
        except Exception as e:
            logging.error(f"Error handling trigger file: {e}")
            return False
    return False

def signal_handler(sig, frame):
    """Handle graceful shutdown."""
    logging.info("Shutting down scraper...")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    while True:
        try:
            if check_trigger_file() or True:  # Run immediately if trigger file exists
                if scrape_pins():
                    logging.info("Scrape cycle completed successfully")
                else:
                    logging.warning("No images downloaded in this cycle")
            else:
                logging.info("No trigger file, waiting for next scheduled cycle")
        except Exception as e:
            logging.error(f"Cycle failed: {e}")
        logging.info(f"Waiting {UPDATE_INTERVAL} seconds for next cycle...")
        for _ in range(UPDATE_INTERVAL // 10):  # Check trigger file every 10 seconds
            if check_trigger_file():
                if scrape_pins():
                    logging.info("Immediate scrape cycle completed successfully")
                else:
                    logging.warning("No images downloaded in immediate cycle")
            time.sleep(10)
