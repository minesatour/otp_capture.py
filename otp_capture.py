import time
import re
import threading
import subprocess
import os
import mitmproxy.http
from mitmproxy import ctx
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class OTPInterceptor:
    """Intercepts OTPs from PayPal's network requests"""

    def __init__(self):
        self.otp_code = None
        self.otp_requested = False
        self.lock = threading.Lock()

    def request(self, flow: mitmproxy.http.HTTPFlow):
        """Intercept HTTP traffic and extract OTP"""
        if "paypal.com/authflow/api/otp/send" in flow.request.pretty_url:
            with self.lock:
                self.otp_requested = True
                print("\n✅ [INFO] OTP request detected. Waiting for OTP response...\n")

        if self.otp_requested and "paypal" in flow.request.pretty_url and ("sms" in flow.request.text or "otp" in flow.request.text):
            otp = self.extract_otp(flow.request.text)
            if otp:
                with self.lock:
                    self.otp_code = otp
                    ctx.log.info(f"[Captured OTP] {otp}")
                    print(f"\n🔐 Captured OTP: {otp}\n")

    def extract_otp(self, text):
        """Extracts OTP from intercepted text using regex"""
        match = re.search(r'\b\d{6}\b', text)  # Match only 6-digit OTP
        return match.group(0) if match else None

# Initialize OTP interceptor
otp_interceptor = OTPInterceptor()

# Start mitmproxy in a separate thread
def start_mitmproxy():
    try:
        subprocess.Popen(["mitmdump", "-s", __file__, "--set", "block_global=false"])
    except Exception as e:
        print(f"[ERROR] Failed to start mitmproxy: {e}")
        os._exit(1)

# Start mitmproxy first
threading.Thread(target=start_mitmproxy, daemon=True).start()

# Wait a bit to ensure mitmproxy starts before Selenium
time.sleep(5)

# Configure Selenium WebDriver
chrome_options = Options()
chrome_options.add_argument("--headless")  # Run browser in the background
chrome_options.add_argument("--log-level=3")  # Suppress logs
chrome_options.add_argument("--proxy-server=http://127.0.0.1:8080")  # Set proxy to mitmproxy's default

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

def wait_for_otp():
    """Waits for OTP after the user requests it"""
    print("[INFO] Waiting for user to request OTP...")

    while not otp_interceptor.otp_requested:
        time.sleep(1)

    print("[INFO] OTP request detected! Listening for OTP...")

    while not otp_interceptor.otp_code:
        time.sleep(1)

    print(f"\n🔐 Captured OTP: {otp_interceptor.otp_code}\n")
    return otp_interceptor.otp_code

# Open PayPal login page
print("[INFO] Launching PayPal...")
driver.get("https://www.paypal.com/uk/signin")
time.sleep(3)

# Let user manually enter login details
input("\nEnter your PayPal email & password manually, then press Enter to continue...")

# Wait for user to request OTP
otp_code = wait_for_otp()

if otp_code:
    input("Enter the OTP on PayPal and press Enter once logged in...")

print("\n✅ Login process complete!")
driver.quit()
