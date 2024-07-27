import asyncio
from agents.browseragent import BrowserAgent, ViewMode
from agents.screen_agent import ScreenAgent
from agents.executeagent import ExecuteAgent

async def simulate():
    page = BrowserAgent('new_agent')

    await page.build(ViewMode.headful, stealth=True)
    await page.newPage()

    screen = ScreenAgent(page.current_page)
    execute = ExecuteAgent(page.current_page)

    screen.set_url('https://mail.google.com')
    await screen.read_page(navigate=True)

    cache_dir = await screen.build_action('enter email as grand.hunter.dark.15@gmail.com and then press the next button')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('enter the password as Grandhunter15 and press the login button')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('press the compose button')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('enter balajirw10@gmail.com in the To field')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('enter Test in the Subject field')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('Enter "I love cats" in the body field')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('send the email')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)


if __name__ == '__main__':
    asyncio.run(simulate())