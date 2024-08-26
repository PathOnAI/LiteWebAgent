from playwright.sync_api import sync_playwright
import os
import threading

class PlaywrightManager:
    def __init__(self, storage_state=None, video_dir='./litewebagent/videos'):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.storage_state = storage_state
        self.video_dir = video_dir
        self.lock = threading.Lock()

        # Ensure the video directory exists
        os.makedirs(self.video_dir, exist_ok=True)

    def initialize(self):
        with self.lock:
            if self.playwright is None:
                self.playwright = sync_playwright().start()
                self.browser = self.playwright.chromium.launch(headless=False)

                context_options = {
                    "record_video_dir": self.video_dir,
                    "record_video_size": {"width": 1280, "height": 720}
                }

                if self.storage_state:
                    context_options["storage_state"] = self.storage_state

                self.context = self.browser.new_context(**context_options)
                self.page = self.context.new_page()

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

# # Initialize the PlaywrightManager with the storage state and video directory
# playwright_manager = PlaywrightManager(storage_state=None, video_dir='./litewebagent/videos')
#
# def get_browser():
#     return playwright_manager.browser
#
# def get_context():
#     return playwright_manager.context
#
# def get_page():
#     return playwright_manager.get_page()
#
# def close_playwright():
#     playwright_manager.close()