import pytest
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from tests.conftest_selenium import FRONTEND_URL


class TestE2ESelenium:
    def test_login_page_renders(self, driver):
        """Test that the login page loads correctly."""
        driver.get(f"{FRONTEND_URL}/login")
        
        wait = WebDriverWait(driver, 10)
        wait.until(EC.title_contains("Legal AI") or EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Legal AI')]")))
        
        # Verify elements exist
        assert driver.find_element(By.XPATH, "//h1[contains(text(), 'Legal AI')]").is_displayed()
        assert driver.find_element(By.XPATH, "//input[@type='email']").is_displayed()
        assert driver.find_element(By.XPATH, "//input[@type='password']").is_displayed()

    def test_navigation_after_login(self, logged_in_driver):
        """Test navigation to different pages from the dashboard."""
        driver = logged_in_driver
        wait = WebDriverWait(driver, 10)
        
        # Ensure we're on dashboard
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Welcome')]")))
        
        # Helper to click a sidebar/nav link and verify title/header
        def test_nav_link(link_text, expected_header):
            link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(., '{link_text}')]")))
            link.click()
            wait.until(EC.presence_of_element_located((By.XPATH, f"//*[contains(text(), '{expected_header}')]")))
            
        test_nav_link("Generate", "Generate Contract")
        
        # Navigate back to dashboard using branding/logo
        home = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/')]")))
        # Need to be careful if multiple href='/' exist, choose first one
        home.click()

    def test_generate_contract_flow(self, logged_in_driver):
        """Test the E2E contract generation flow."""
        driver = logged_in_driver
        wait = WebDriverWait(driver, 10)
        
        # Navigate to generator
        driver.get(f"{FRONTEND_URL}/generate")
        wait.until(EC.presence_of_element_located((By.XPATH, "//h1[contains(text(), 'Generate Contract')]")))
        
        # Fill in form
        
        # 1. Title
        title_input = driver.find_element(By.XPATH, "//label[contains(text(), 'Title')]/following-sibling::input")
        title_input.send_keys("E2E Test NDA Agreement")
        
        # 2. Parties
        party_inputs = driver.find_elements(By.XPATH, "//input[contains(@placeholder, 'Party name')]")
        if len(party_inputs) >= 2:
            party_inputs[0].send_keys("E2E Corp")
            party_inputs[1].send_keys("Test LLC")
            
        # 3. Submit
        submit_btn = driver.find_element(By.XPATH, "//button[@type='submit']")
        driver.execute_script("arguments[0].scrollIntoView();", submit_btn)
        time.sleep(0.5) # allow smooth scroll
        submit_btn.click()
        
        # 4. Verify generation success (navigation to contract view or success toast)
        wait.until(lambda d: "contracts/" in d.current_url or EC.presence_of_element_located((By.XPATH, "//*[contains(text(), 'success')]")))
        
