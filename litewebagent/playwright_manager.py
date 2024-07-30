from playwright.sync_api import sync_playwright

class PlaywrightManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    def initialize(self):
        if self.playwright is None:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)  # Set headless to False
            self.page = self.browser.new_page()

    def get_page(self):
        if self.page is None:
            self.initialize()
        return self.page

    def close(self):
        if self.page:
            self.page.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        self.page = None
        self.browser = None
        self.playwright = None

playwright_manager = PlaywrightManager()

def get_page():
    return playwright_manager.get_page()

def close_playwright():
    playwright_manager.close()