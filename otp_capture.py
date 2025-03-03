import time
import logging
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database setup
def create_db():
    conn = sqlite3.connect("otp_codes.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS otp_codes
                      (id INTEGER PRIMARY KEY, otp TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def save_otp(otp_code):
    conn = sqlite3.connect("otp_codes.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO otp_codes (otp) VALUES (?)", (otp_code,))
    conn.commit()
    conn.close()

# Setting up Chrome WebDriver with increased timeout
def init_driver():
    options = Options()
    options.add_argument("--headless")  # Run in headless mode
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.set_page_load_timeout(180)  # Increase page load timeout
    return driver

# Intercept OTP from page content
def capture_otp(driver, url):
    driver.get(url)
    logging.info("Page loaded successfully.")
    
    # Example: Look for OTP input field or trigger an event
    try:
        otp_input = driver.find_element(By.NAME, "otp")  # Modify as per actual element
        otp_code = otp_input.get_attribute('value')
        
        if otp_code:
            logging.info(f"Captured OTP: {otp_code}")
            save_otp(otp_code)
        else:
            logging.warning("OTP not found or input is empty.")
    except Exception as e:
        logging.error(f"Error capturing OTP: {str(e)}")

# Example of handling OTP capture from a request API (e.g., email provider)
def capture_otp_from_api(api_url, headers, params):
    try:
        response = requests.get(api_url, headers=headers, params=params)
        if response.status_code == 200:
            otp_code = response.text  # Assuming OTP is returned in the body (adjust as needed)
            logging.info(f"Captured OTP from API: {otp_code}")
            save_otp(otp_code)
        else:
            logging.warning("Failed to capture OTP from API.")
    except Exception as e:
        logging.error(f"Error capturing OTP from API: {str(e)}")

# Main execution
def main():
    create_db()
    
    # URL for OTP capture (modify for your use case)
    otp_page_url = "https://example.com/otp"
    
    # API parameters (modify based on your API requirements)
    api_url = "https://api.example.com/otp"
    headers = {'Authorization': 'Bearer YOUR_API_KEY'}
    params = {'user_id': 'user123'}

    driver = init_driver()

    try:
        # Capture OTP from the website
        capture_otp(driver, otp_page_url)
        
        # Optionally capture OTP from an API (if applicable)
        capture_otp_from_api(api_url, headers, params)
    
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
