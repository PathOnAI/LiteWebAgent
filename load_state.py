import asyncio
from playwright.async_api import async_playwright
import json
import argparse


async def handle_login_state(action):
    terminated = False
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        if action == 'save':
            context = await browser.new_context()
        elif action == 'load':
            context = await browser.new_context(storage_state='state.json')

        page = await context.new_page()
        await page.goto('https://www.amazon.com')

        print(f"Browser opened. Close the browser window to {action} the storage state.")

        async def save_storage_state(_):
            nonlocal terminated
            state = await context.storage_state()
            print('Saving storage state', state)
            with open('state.json', 'w') as f:
                json.dump(state, f, indent=4)
            await context.close()
            terminated = True

        page.on('close', save_storage_state)

        try:
            while not terminated:
                await asyncio.sleep(1)
            await browser.close()
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description="Save or load login state for ClickUp")
    parser.add_argument('action', choices=['save', 'load'], help="Action to perform: save or load login state")
    args = parser.parse_args()

    asyncio.run(handle_login_state(args.action))


if __name__ == "__main__":
    main()