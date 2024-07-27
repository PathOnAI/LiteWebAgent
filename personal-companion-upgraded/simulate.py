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

    screen.set_url('https://www.discord.com/login')
    await screen.read_page(navigate=True)

    cache_dir = await screen.build_action('enter email as izzyelwood37@gmail.com and password as IzzyColon2024 and then press the login button')
    await execute.load(cache_dir).call()
    await asyncio.sleep(5)

    cache_dir = await screen.build_action('select user airborn')
    await execute.load(cache_dir).call()
    await asyncio.sleep(3)

    cache_dir = await screen.build_action('send message "hello from agent"')
    await execute.load(cache_dir).call()
    await asyncio.sleep(3)


if __name__ == '__main__':
    asyncio.run(simulate())