import asyncio
from playwright.async_api import async_playwright, Page

from agents.screen_agent import ScreenAgent
from agents.execute_agent import ExecuteAgent
from agents.page_agent import PageAgent, ViewMode
from agents.workflow_agent import WorkflowAgent

from imports import *

def append_to_file(file_path, text):
    with open(file_path, 'a') as file:
        file.write(text + '\n')

async def simulate():
    page = PageAgent('new_agent')

    await page.build(ViewMode.headful, stealth=True)
    await page.newPage()

    screen = ScreenAgent(page.current_page)
    execute = ExecuteAgent(page.current_page)
    workflow = WorkflowAgent()

    workflow.set_goal("""
    log into my discord account, email is izzyelwood37@gmail.com and password is IzzyColon2024
    and then send message "Sent By Agent haha" to Airborn
    """)

    screen.set_url('https://www.google.com')
    await screen.read_page(navigate=True)

    failed = False

    while True:
        await screen.read_page(navigate=False)
        step = workflow.propose_action()

        if step is None:
            break
        
        if failed:
            cache_dir = await screen.build_action(step, code_path=f'{screen.function_root}{cache_dir}.py')
        else:
            cache_dir = await screen.build_action(step)

        try:
            await execute.load(cache_dir).call()
            append_to_file(f'{os.path.dirname(os.path.abspath(__file__))}/cache/steps.txt', step)
            failed = False
        except:
            print('Auto-Resolved')
            failed = True
            workflow.propose_resolution(code_path=f'{screen.function_root}{cache_dir}.py')

        await asyncio.sleep(3)


    await asyncio.sleep(10)
    
    

    

    await page.close()
    

asyncio.run(simulate())