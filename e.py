from playwright.sync_api import sync_playwright

from litewebagent.webagent_utils_sync.utils.playwright_manager import setup_playwright

playwright_manager = setup_playwright(
        log_folder='/',
        storage_state='state.json',
        headless=False,
        mode="cdp"
    )

print(playwright_manager)