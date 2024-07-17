async def navigate_to_amazon(page):
    elements = await page.query_selector_all(".MV3Tnb")
    await elements[1].click()
    await page.wait_for_load_state("domcontentloaded")
    await page.goto("https://www.amazon.com")