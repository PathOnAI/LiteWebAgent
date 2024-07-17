async def click_first_product(page):
    await page.wait_for_load_state("domcontentloaded")
    elements = await page.locator(".s-result-item").all()
    await elements[0].click()