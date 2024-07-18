async def click_sign_in(page):
    elements = await page.locator(".vAV9bf").all()
    await elements[0].click()