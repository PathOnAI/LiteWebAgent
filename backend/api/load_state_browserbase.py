import asyncio
from playwright.async_api import async_playwright
import json
import argparse
import os
from dotenv import load_dotenv
import aiohttp

# Load environment variables from .env file
load_dotenv()

API_KEY = os.environ["BROWSERBASE_API_KEY"]
PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

async def create_session() -> str:
    """
    Create a Browserbase session - a single browser instance.
    
    :returns: The new session's ID.
    """
    sessions_url = "https://www.browserbase.com/v1/sessions"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    json = {"projectId": PROJECT_ID}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(sessions_url, json=json, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["id"]

async def get_browser_url(session_id: str) -> str:
    """
    Get the URL to show the live view for the current browser session.
    
    :returns: URL
    """
    session_url = f"https://www.browserbase.com/v1/sessions/{session_id}/debug"
    headers = {
        "Content-Type": "application/json",
        "x-bb-api-key": API_KEY,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(session_url, headers=headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data["debuggerFullscreenUrl"]

async def handle_login_state(action):
    terminated = False
    
    async with async_playwright() as p:
        try:
            session_id = await create_session()
            live_browser_url = await get_browser_url(session_id)
            print(f"Live browser URL: {live_browser_url}")

            browser = await p.chromium.connect_over_cdp(
                f"wss://connect.browserbase.com?apiKey={API_KEY}&sessionId={session_id}"
            )

            context_options = {}
            if action == 'load':
                try:
                    with open('state.json', 'r') as f:
                        storage_state = json.load(f)
                    context_options['storage_state'] = storage_state
                    print("Loading stored state from state.json")
                except FileNotFoundError:
                    print("Warning: state.json not found. Starting with fresh context.")

            context = await browser.new_context(**context_options)
            page = await context.new_page()
            
            print(f"Navigating to Loggia...")
            await page.goto('https://app.loggia.ai')
            await asyncio.sleep(5)  # Wait 5 seconds after loading Loggia
            print("Navigation complete")
            print(f"Navigating to amazon...")
            await page.goto('https://www.amazon.com/')
            await asyncio.sleep(5)  # Wait 5 seconds after loading Loggia
            print("Navigation complete")
            print(f"Navigating to google...")
            await page.goto('https://www.google.com/')
            await asyncio.sleep(5)  # Wait 5 seconds after loading Loggia
            print("Navigation complete")

            async def handle_page_close(page):
                nonlocal terminated
                if action == 'save':
                    print("Saving storage state...")
                    state = await context.storage_state()
                    with open('state.json', 'w') as f:
                        json.dump(state, f, indent=4)
                    print("Storage state saved to state.json")
                terminated = True

            page.on('close', handle_page_close)

            print(f"Browser opened. Close the browser window to {action} the storage state.")
            while not terminated:
                await asyncio.sleep(1)

        except Exception as e:
            print(f"An error occurred: {str(e)}")
            raise
        finally:
            if 'browser' in locals():
                await browser.close()
            print("Browser session terminated")

def main():
    parser = argparse.ArgumentParser(description="Save or load login state for Loggia")
    parser.add_argument('action', choices=['save', 'load'], 
                       help="Action to perform: save or load login state")
    args = parser.parse_args()
    
    asyncio.run(handle_login_state(args.action))

if __name__ == "__main__":
    main()