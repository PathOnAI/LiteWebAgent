async def search_test(page):
    await page.wait_for_load_state('domcontentloaded')
    await page.fill("#twotabsearchtextbox", "dining table")
    await page.click("#nav-search-submit-button")