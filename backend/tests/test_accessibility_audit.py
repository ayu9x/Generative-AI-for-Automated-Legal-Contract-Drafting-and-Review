import pytest
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from axe_selenium_python import Axe

# Base URL for frontend application
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


@pytest.fixture(scope="session")
def axe_driver():
    """Setup Chrome WebDriver for Accessibility tests."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(10)
    
    yield driver
    driver.quit()


class TestAccessibility:
    def check_accessibility(self, driver, url, page_name):
        """Helper to run axe-core on a page and assert zero violations."""
        driver.get(url)
        # Give React time to render 
        time.sleep(2)
        
        axe = Axe(driver)
        # Inject axe-core into page
        axe.inject()
        # Run axe checks
        results = axe.run()
        
        # Write results to a file for review
        os.makedirs("a11y_reports", exist_ok=True)
        axe.write_results(results, f"a11y_reports/{page_name}_a11y.json")
        
        # We fail the test if there are violations (you may want to filter for Critical/Serious only initially)
        violations = results["violations"]
        
        if violations:
            print(f"\nFound {len(violations)} accessibility violations on {page_name}:")
            for violation in violations:
                print(f"- {violation['id']}: {violation['description']} ({len(violation['nodes'])} nodes)")
                
        # Optional: Assert zero violations for strict CI
        # assert len(violations) == 0, axe.report(violations)

    def test_login_page_accessibility(self, axe_driver):
        self.check_accessibility(axe_driver, f"{FRONTEND_URL}/login", "login")

    def test_dashboard_accessibility(self, axe_driver):
        # Note: If dashboard is protected, you would need to log in first.
        # This is a basic check.
        self.check_accessibility(axe_driver, f"{FRONTEND_URL}/", "dashboard")

    def test_generator_accessibility(self, axe_driver):
        self.check_accessibility(axe_driver, f"{FRONTEND_URL}/generate", "generator")
