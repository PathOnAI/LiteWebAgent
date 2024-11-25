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

# TODO: change to use the page that corresponds to active tab
def get_non_extension_context_and_page(browser):
    """
    Get the first context and page that don't belong to a Chrome extension.
    
    Args:
        browser: Playwright browser instance
    Returns:
        tuple: (context, page) or (None, None) if not found
    """
    for context in browser.contexts:
        for page in context.pages:
            if not page.url.startswith("chrome-extension://"):
                return context, page
    return None, None

class PlaywrightManager:
    def __init__(self, storage_state=None, headless=False, mode="chromium"):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.lock = threading.Lock()
        self.headless = headless
        self.mode = mode
    
    def initialize(self):
        with self.lock:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
                
                if self.mode == "cdp":
                    chrome_url = "http://localhost:9222"
                    self.browser = self.playwright.chromium.connect_over_cdp(chrome_url)
                    debug_browser_state(self.browser)
                    
                    # Get non-extension context and page
                    self.context, self.page = get_non_extension_context_and_page(self.browser)
                    if not self.context or not self.page:
                        raise ValueError("No non-extension context and page found in CDP browser")
                    
                    debug_browser_state(self.browser)
                
                elif self.mode == "chromium":
                    self.browser = self.playwright.chromium.launch(headless=self.headless)
                    context_options = {}
                    
                    if self.storage_state:
                        context_options["storage_state"] = self.storage_state
                    
                    self.context = self.browser.new_context(**context_options)
                    self.page = self.context.new_page()
                    
                else:
                    raise ValueError(f"Invalid mode: {self.mode}. Expected 'cdp' or 'chromium'")
    
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

def setup_playwright(log_folder, storage_state='state.json', headless=False, mode="chromium"):
    playwright_manager = PlaywrightManager(storage_state=storage_state, headless=headless, mode=mode)
    browser = playwright_manager.get_browser()
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    return playwright_manager
