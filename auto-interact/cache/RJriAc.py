async def fill_password(page):
    elements = await page.locator("input[name='hiddenPassword']").all()
    await elements[0].fill("D4c3b2a1#")