from playwright.async_api import async_playwright, Page, Route
from undetected_playwright import Malenia
import asyncio
import os
from enum import Enum

class ViewMode(str, Enum):
    new = "new"
    headless = "headless"
    headful = "headful"

class PageAgent:
    def __init__(self, name: str):
        self.name = name

    async def build(self, view_mode: ViewMode, stealth=False):
        self.p = await async_playwright().start()
        match view_mode:
            case "new":
                args = ["--headless=new", "--dump-dom", "--disable-blink-features=AutomationControlled"]
                self.browser = await self.p.chromium.launch(args=args)
            case "headless":
                args = ["--disable-blink-features=AutomationControlled"]
                self.browser = await self.p.chromium.launch(headless=True, args=args)
            case _:
                args = ["--disable-blink-features=AutomationControlled"]
                self.browser = await self.p.chromium.launch(headless=False, args=args)
            
        self.context = await self.browser.new_context(locale="en-US", no_viewport=True)

        if stealth:
            await Malenia.apply_stealth(self.context)

        self.pages = {}

    async def newPage(self, key: str = 'new_page', fresh=False):
        self.current_page = await self.context.new_page()
        self.pages[key] = self.current_page

        if fresh:
            await self.current_page.goto('https://www.google.com', wait_until="networkidle")

        return self
    

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.p.stop()

        return self
    
