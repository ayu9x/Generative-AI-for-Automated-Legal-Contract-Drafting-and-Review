import pytest
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Base URL for frontend application
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def driver():
    """Setup Chrome WebDriver for E2E tests."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Set implicit wait
    driver.implicitly_wait(10)

    yield driver

    driver.quit()


@pytest.fixture
def logged_in_driver(driver):
    """Fixture that logs in a user and returns the driver."""
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    
    # Needs a real user sequence in the application
    driver.get(FRONTEND_URL + "/login")
    
    # Wait for the login form to be present
    wait = WebDriverWait(driver, 10)
    email_input = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='email']")))
    
    # Switch to register to ensure we have an account for testing
    register_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'register') or contains(text(), 'Register')]")
    register_btn.click()
    
    # Fill registration (which acts as login)
    wait.until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='John Doe']"))).send_keys("E2E Test User")
    driver.find_element(By.XPATH, "//input[@type='email']").send_keys("e2e@test.com")
    driver.find_element(By.XPATH, "//input[@type='password']").send_keys("securepass123")
    
    # Submit
    driver.find_element(By.XPATH, "//button[@type='submit']").click()
    
    # Wait for navigation to dashboard (or toast to vanish)
    wait.until(lambda d: "login" not in d.current_url.lower())
    
    yield driver
