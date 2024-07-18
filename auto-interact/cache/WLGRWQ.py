async def google_search(page):
    await page.goto("https://www.google.com/", wait_until="domcontentloaded")
    await page.fill("input[name='q']", "cows")
    await page.click("input[name='btnK']")