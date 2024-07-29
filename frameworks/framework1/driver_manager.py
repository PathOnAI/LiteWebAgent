from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

driver = None

def initialize_driver():
    global driver
    if driver is None:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service)
    return driver

def get_driver():
    global driver
    if driver is None:
        return initialize_driver()
    return driver

def quit_driver():
    global driver
    if driver:
        driver.quit()
        driver = None