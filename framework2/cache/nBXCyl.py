async def search_test(page):
    elements = await page.query_selector_all("#twotabsearchtextbox")
    await elements[0].fill("dining table")
    elements = await page.query_selector_all("#nav-search-submit-button")
    await elements[0].click()
    await page.wait_for_load_state("domcontentloaded")