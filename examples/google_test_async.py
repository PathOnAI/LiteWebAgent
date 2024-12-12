from dotenv import load_dotenv
_ = load_dotenv()
from litewebagent_async.core.agent_factory import setup_function_calling_web_agent
from litewebagent_async.webagent_utils_async.utils.playwright_manager import setup_playwright
import asyncio

async def main():
    playwright_manager = await setup_playwright(storage_state='state.json', headless=False, mode="chromium")

    starting_url = "https://www.google.com"
    goal = 'search dining table, and click on the 1st result'
    plan = None
    agent_type = "FunctionCallingAgent"
    model = "gpt-4o-mini"
    features = "axtree"
    log_folder = "log"
    elements_filter = "som"

    agent = await setup_function_calling_web_agent(
        starting_url,
        goal,
        playwright_manager=playwright_manager,
        model_name=model,
        agent_type=agent_type,
        features=features,
        tool_names=["navigation", "select_option", "upload_file"],
        log_folder=log_folder,
        elements_filter=elements_filter
    )

    response = await agent.send_prompt(plan)  # Added await here
    print(response)

    # Close the playwright_manager when done
    await playwright_manager.close()  # Added await here

if __name__ == "__main__":
    asyncio.run(main())