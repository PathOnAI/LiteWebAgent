async def enter_email(page):
    elements = await page.locator("input[name='identifier']").all()
    await elements[0].fill('balajirw10@gmail.com')