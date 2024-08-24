from litewebagent.playwright_manager import PlaywrightManager
playwright_manager = PlaywrightManager(storage_state=None, video_dir='./litewebagent/videos')
page = playwright_manager.get_page()
starting_url = "https://www.google.com"
page.goto(starting_url)
playwright_manager.close()

playwright_manager = PlaywrightManager(storage_state=None)
page = playwright_manager.get_page()
starting_url = "https://www.google.com"
page.goto(starting_url)
playwright_manager.close()

# from playwright.sync_api import sync_playwright
#
# playwright = sync_playwright().start()
# browser = playwright.chromium.launch(headless=False)
# page = browser.new_page()
# page.goto("https://playwright.dev/")
# page.screenshot(path="example.png")
# browser.close()
# playwright.stop()
#
#
# playwright = sync_playwright().start()
# browser = playwright.chromium.launch(headless=False)
# page = browser.new_page()
# page.goto("https://www.amazon.com/")
# page.screenshot(path="example.png")
# browser.close()
# browser.close()
# playwright.stop()
