from playwright.sync_api import sync_playwright

def test_google_search():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        # Navigate to Google's homepage
        page.goto('https://www.google.com')

        # Wait for the search input (textarea) to appear
        page.wait_for_selector('textarea[name="q"]')

        # Type in a search query
        page.fill('textarea[name="q"]', 'Playwright testing')

        # Press Enter to perform the search
        page.press('textarea[name="q"]', 'Enter')

        # Wait for the search results to load
        page.wait_for_selector('h3')

        # Check if the first result contains the expected text
        first_result = page.text_content('h3')
        print(first_result)
        assert 'Playwright' in first_result

        browser.close()

if __name__ == "__main__":
    test_google_search()
