async def scroll_to_add_to_cart(page):
    await page.wait_for_load_state("domcontentloaded")
    elements = await page.locator("#submit.add-to-cart").all()
    await elements[0].scroll_into_view_if_needed()