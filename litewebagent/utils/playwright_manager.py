import os
import threading
from playwright.sync_api import sync_playwright

def debug_browser_state(browser):
    """
    Print detailed information about browser contexts and their pages.
    """
    print("\n=== Browser State Debug ===")
    
    # List all contexts
    contexts = browser.contexts
    print(f"\nTotal contexts: {len(contexts)}")
    
    for i, context in enumerate(contexts):
        print(f"\nContext {i}:")
        pages = context.pages
        print(f"- Number of pages: {len(pages)}")
        
        for j, page in enumerate(pages):
            print(f"  - Page {j}: {page.url}")
            
    print("\n========================")

class PlaywrightManager:
    def __init__(self, storage_state=None, headless=False):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.lock = threading.Lock()
        self.headless = headless

    def initialize(self):
        with self.lock:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
                # self.browser = self.playwright.chromium.launch(headless=self.headless)
                chrome_url = "http://localhost:9222"
                self.browser = self.playwright.chromium.connect_over_cdp(chrome_url)

                # context_options = {}

                # if self.storage_state:
                #     context_options["storage_state"] = self.storage_state

                # self.context = self.browser.new_context(**context_options)
                # self.page = self.context.new_page()
                debug_browser_state(self.browser)
                self.context = self.browser.contexts[0]
                self.page = self.context.pages[0]
                debug_browser_state(self.browser)


    def get_browser(self):
        if self.browser is None:
            self.initialize()
        return self.browser

    def get_context(self):
        if self.context is None:
            self.initialize()
        return self.context

    def get_page(self):
        if self.page is None:
            self.initialize()
        return self.page

    def close(self):
        with self.lock:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()

            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None


def setup_playwright(log_folder, storage_state='state.json', headless=False):
    playwright_manager = PlaywrightManager(storage_state=storage_state, headless=headless)
    browser = playwright_manager.get_browser()
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    return playwright_manager
