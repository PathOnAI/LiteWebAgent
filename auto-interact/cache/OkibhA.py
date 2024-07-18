async def click_next(page):
    elements = await page.locator(".VfPpkd-LgbsSe").all()
    await elements[0].click()