async def search_test(page):
    await page.wait_for_load_state('domcontentloaded')
    elements = await page.locator(".s-result-item").all()
    random_index = random.randint(0, len(elements) - 1)
    await elements[random_index].click()