async def fill_email(page):
    elements = await page.locator("input[name='identifier']").all()
    await elements[0].fill("izzyelwood37@gmail.com")