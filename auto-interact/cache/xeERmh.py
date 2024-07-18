async def google_search(page):
    await page.goto("https://accounts.google.com/ServiceLogin?hl=en&passive=true&continue=https://www.google.com/&ec=GAZAmgQ", wait_until="domcontentloaded")