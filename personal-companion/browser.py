import asyncio
import os
from enum import Enum
from datetime import datetime
from playwright.async_api import async_playwright, Page, Route
import base64
from undetected_playwright import Malenia
import difflib
from bs4 import BeautifulSoup
import re

from reader import ReaderAgent

from dotenv import load_dotenv

load_dotenv()


class ViewMode(str, Enum):
    new = "new"
    headless = "headless"
    headful = "headful"


class InteractFlow:
    async def build(self, view_mode: ViewMode, output_dir: str = 'screenshots', interval: float = 0.1):
        self.p = await async_playwright().start()
        match view_mode:
            case "new":
                args = ["--headless=new", "--dump-dom"]
                self.browser = await self.p.chromium.launch(args=args)
            case "headless":
                self.browser = await self.p.chromium.launch(headless=True)
            case _:
                args = ["--disable-blink-features=AutomationControlled"]
                self.browser = await self.p.chromium.launch(headless=False, args=args)

        self.context = await self.browser.new_context(locale="en-US", no_viewport=True)
        self.context.on("page", self.handle_new_page)
        await Malenia.apply_stealth(self.context)

        self.pages = {}
        self.frames = []
        self.current_page = None
        self._stop_event = asyncio.Event()
        self.frame_count = 0
        self.output_dir = output_dir
        self.interval = interval
        self.last_url = ''
        self.last_screenshot_hash = ''
        self.reader = ReaderAgent()

        return self

    async def handle_new_page(self, page):
        self.current_page = page

    async def newPage(self, key: str):
        self.current_page = await self.context.new_page()
        self.pages[key] = self.current_page
        await self.current_page.goto('https://www.google.com', wait_until="networkidle")

        return self

    async def start_monitoring(self):
        # Set up event listeners
        self.current_page.on("load", self.on_load)
        self.current_page.on("framenavigated", self.on_frame_navigated)

        while not self._stop_event.is_set():
            await self.check_and_save_content()
            await asyncio.sleep(self.interval)

    async def close(self):
        await self.context.close()
        await self.browser.close()
        await self.p.stop()

        return self
    
    def html_similarity(self, html1, html2, threshold=0.9):
        def clean_html(html):
            try:
                # Use 'html.parser' which is more lenient
                soup = BeautifulSoup(html, 'html.parser')
                # Extract text, including from script and style tags
                for script in soup(["script", "style"]):
                    script.extract()
                text = soup.get_text()
                # Normalize whitespace
                text = re.sub(r'\s+', ' ', text).strip()
                return text
            except Exception as e:
                print(f"Warning: Error parsing HTML: {e}")
                # If parsing fails, return the original string with basic cleaning
                return re.sub(r'\s+', ' ', html).strip()

        text1 = clean_html(html1)
        text2 = clean_html(html2)

        similarity = difflib.SequenceMatcher(None, text1, text2).ratio()

        return similarity >= threshold, similarity

    async def on_load(self, event):
        await self.check_and_save_content()

    async def on_frame_navigated(self, frame):
        if frame == self.current_page.main_frame:
            await self.check_and_save_content()

    async def check_and_save_content(self):
        main_content = await self.current_page.evaluate('''() => {
                let main = document.querySelector('main');
                if (!main) {
                    main = document.body;  
                }
                
                const clone = main.cloneNode(true);

                const unwantedTags = ['script', 'style', 'link', 'meta', 'noscript', 'iframe'];
                unwantedTags.forEach(tag => {
                    clone.querySelectorAll(tag).forEach(el => el.remove());
                });
                                                    
                clone.querySelectorAll('svg').forEach(svg => {
                    while (svg.firstChild) {
                        svg.removeChild(svg.firstChild);
                    }
                });

                // Remove data- attributes and limit classes to 3
                clone.querySelectorAll('*').forEach(el => {
                    [...el.attributes].forEach(attr => {
                        if (attr.name.startsWith('data-')) {
                            el.removeAttribute(attr.name);
                        } else if (attr.name === 'class') {
                            let classes = attr.value.split(/\s+/);
                            if (classes.length > 3) {
                                el.className = classes.slice(0, 3).join(' ');
                            }
                        }
                    });
                });

                return clone.innerHTML;
            }''')
        
        is_sim, raw_sim = self.html_similarity(self.last_screenshot_hash, main_content)

        if not is_sim:
            self.last_screenshot_hash = main_content
            self.reader.read_schema(self.last_screenshot_hash)


    async def save_screenshot(self, screenshot_data):
        current_url = self.current_page.url
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = f"frame_{self.frame_count:05d}_{timestamp}.png"
        path = os.path.join('screenshots', filename)

        with open(path, "wb") as f:
            f.write(base64.b64decode(screenshot_data))
        self.frame_count += 1

        if current_url != self.last_url:
            print(f"URL changed to: {current_url}")
            self.last_url = current_url

    async def lock(self):
        try:
            await self._stop_event.wait()
        except KeyboardInterrupt:
            print("Closing browser...")
        finally:
            await self.close()


async def main():
    flow = InteractFlow()
    await flow.build(ViewMode.headful, interval=1)
    await flow.newPage('first')
    await flow.start_monitoring()
    await flow.lock()


if __name__ == "__main__":
    asyncio.run(main())
