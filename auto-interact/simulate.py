import asyncio
from playwright.async_api import async_playwright, Page

from agents.screen_agent import ScreenAgent
from agents.execute_agent import ExecuteAgent
from agents.page_agent import PageAgent, ViewMode
from agents.workflow_agent import WorkflowAgent

from imports import *

async def search_test(page):
    await page.fill("#twotabsearchtextbox", "dining table")
    await page.click("#nav-search-submit-button")

async def simulate():
    page = PageAgent('new_agent')

    await page.build(ViewMode.headful, stealth=True)
    await page.newPage()

    screen = ScreenAgent(page.current_page)
    execute = ExecuteAgent(page.current_page)
    workflow = WorkflowAgent()

    workflow.set_goal("""
    log into my gmail account and send an email to grand.hunter.dark.15@gmail.com with Subject of 'Test' \
    and content of "This is a test email"
    , my username is balajirw10@gmail.com and my password is D4c3b2a1#
    """)

    screen.set_url('https://www.google.com')
    await screen.read_page(navigate=True)

    while True:
        await screen.read_page(navigate=False)
        step = workflow.propose_action()

        if step is None:
            break

        cache_dir = await screen.build_action(step)

        try:
            await execute.load(cache_dir).call()
        except:
            print('Auto-Resolved')
            workflow.propose_resolution()

        await asyncio.sleep(3)


    await asyncio.sleep(10)
    
    

    

    await page.close()
    

asyncio.run(simulate())