from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv
import aiohttp
import asyncio

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

async def create_session() -> str:
    """
    Create a Browserbase session - a single browser instance.

    :returns: The new session's ID.
    """
    sessions_url = "https://www.browserbase.com/v1/sessions"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    json = {"projectId": PROJECT_ID}

    async with aiohttp.ClientSession() as session:
        async with session.post(sessions_url, json=json, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["id"]

async def get_browser_url(session_id: str) -> str:
    """
    Get the URL to show the live view for the current browser session.

    :returns: URL
    """
    session_url = f"https://www.browserbase.com/v1/sessions/{session_id}/debug"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(session_url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["debuggerFullscreenUrl"]

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



class PlaywrightManager:
    def __init__(self, storage_state=None, session_id=None):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.session_id = session_id
        self.live_browser_url = None

    async def initialize(self, reinitialization=True):
        """
        Initialize the Playwright manager.
        
        :param reinitialization: If True, creates new context and page. 
                            If False, reuses existing context and page if available.
        """
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            if self.session_id is None:
                self.session_id = await create_session()
            else:
                print("session id is not None")
            self.live_browser_url = await get_browser_url(self.session_id)

            self.browser = await self.playwright.chromium.connect_over_cdp(
                f"wss://connect.browserbase.com?apiKey={API_KEY}&sessionId={self.session_id}"
            )
            # Usage example:
            await debug_browser_state(self.browser)

            if self.storage_state:
                if reinitialization:
                    # Create new context with storage state if provided
                    context_options = {}
                    if self.storage_state:
                        context_options["storage_state"] = self.storage_state
                        print(f"Using storage state from: {self.storage_state}")

                    self.context = await self.browser.new_context(**context_options)
                    self.page = await self.context.new_page()
                else:
                    for context in self.browser.contexts:
                        for page in context.pages:
                            if page.url != "about:blank":
                                self.context = context
                                self.page = page
            else:
                self.context = self.browser.contexts[0]
                self.page = self.context.pages[0]
            
            await debug_browser_state(self.browser)
            
            print(self.context)
            print(self.page)

    async def get_live_browser_url(self):
        self.live_browser_url = await get_browser_url(self.session_id)
        return self.live_browser_url

    def get_session_id(self):
        return self.session_id

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
            print("the page is None")
            await self.initialize()
        return self.page

    async def close(self):
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

async def setup_playwright(session_id=None, storage_state=None, reinitialization=True):
    playwright_manager = PlaywrightManager(session_id=session_id, storage_state=storage_state)
    await playwright_manager.initialize(reinitialization=reinitialization)
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    return playwright_manager