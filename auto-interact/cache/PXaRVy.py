async def sign_in_button(page):
    elements = await page.locator(".gb_ua").all()
    await elements[0].click()