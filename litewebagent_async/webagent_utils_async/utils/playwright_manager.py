import os
import asyncio
from playwright.async_api import async_playwright

async def debug_browser_state(browser):
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
async def get_non_extension_context_and_page(browser):
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

class AsyncPlaywrightManager:
    def __init__(self, storage_state=None, headless=False, mode="chromium"):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.lock = asyncio.Lock()
        self.headless = headless
        self.mode = mode
    
    async def initialize(self):
        async with self.lock:
            if self.playwright is None:
                self.playwright = await async_playwright().start()
                
                if self.mode == "cdp":
                    chrome_url = "http://localhost:9222"
                    self.browser = await self.playwright.chromium.connect_over_cdp(chrome_url)
                    print('debug mode entered')
                    await debug_browser_state(self.browser)
                    
                    # Get non-extension context and page
                    self.context, self.page = await get_non_extension_context_and_page(self.browser)
                    if not self.context or not self.page:
                        raise ValueError("No non-extension context and page found in CDP browser")
                    
                    await debug_browser_state(self.browser)
                
                elif self.mode == "chromium":
                    self.browser = await self.playwright.chromium.launch(headless=self.headless)
                    context_options = {}
                    
                    if self.storage_state:
                        context_options["storage_state"] = self.storage_state
                    
                    self.context = await self.browser.new_context(**context_options)
                    self.page = await self.context.new_page()
                    
                else:
                    raise ValueError(f"Invalid mode: {self.mode}. Expected 'cdp' or 'chromium'")
    
    async def get_browser(self):
        if self.browser is None:
            await self.initialize()
        return self.browser
    
    async def get_context(self):
        if self.context is None:
            await self.initialize()
        return self.context
    
    async def get_page(self):
        if self.page is None:
            await self.initialize()
        return self.page
    
    async def close(self):
        async with self.lock:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            self.page = None
            self.context = None
            self.browser = None
            self.playwright = None

async def setup_playwright(storage_state='state.json', headless=False, mode="chromium"):
    playwright_manager = AsyncPlaywrightManager(storage_state=storage_state, headless=headless, mode=mode)
    browser = await playwright_manager.get_browser()
    context = await playwright_manager.get_context()
    page = await playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    return playwright_manager