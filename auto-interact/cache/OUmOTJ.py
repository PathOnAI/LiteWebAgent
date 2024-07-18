async def navigate_to_google(page):
    await page.goto("https://www.google.com/")
    await page.wait_for_load_state("domcontentloaded")