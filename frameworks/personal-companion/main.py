import asyncio
from flows.interact import InteractFlow, ViewMode

import asyncio
from playwright.async_api import async_playwright, Page

from agents.screen_agent import ScreenAgent
from agents.execute_agent import ExecuteAgent
from agents.reader import ReaderAgent
from agents.workflow_agent import WorkflowAgent

import os

def append_to_file(file_path, text):
    with open(file_path, 'a') as file:
        file.write(text + '\n')
    


async def main():
    flow = InteractFlow()
    await flow.build(ViewMode.headful, interval=1)
    await flow.newPage('first')
    await flow.start_monitoring()
    page = await flow.lock()

    print("<<<<<================>>>>>>")
    print("<<<<<================>>>>>>")
    print("     AGENT ACTIVATED       ")
    print("<<<<<================>>>>>>")
    print("<<<<<================>>>>>>")

    screen = ScreenAgent(page)
    execute = ExecuteAgent(page)
    workflow = WorkflowAgent()

    data: list[dict] = ReaderAgent.read_webpage_info('ephemeral_cache/path.txt')

    workflow.set_goal(flow.steps.get('purpose'), data[-1].get('name'))

    failed = False

    while True:
        await screen.read_page(navigate=False)
        step = workflow.propose_action()

        if step is None:
            break
        
        if failed:
            # cache_dir = await screen.build_action(step, code_path=f'{screen.function_root}{cache_dir}.py')
            cache_dir = await screen.build_action(step)
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
    
    await asyncio.sleep(5)


if __name__ == "__main__":
    asyncio.run(main())
