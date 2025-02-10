from dotenv import load_dotenv
_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.utils.playwright_manager import setup_playwright
import asyncio

async def main():
    import boto3

    # Assumes credentials are set as environment variables or in ~/.aws/credentials
    s3 = boto3.client('s3')

    bucket_name = 'loggia-tests'
    prefix = 'loggia-test/tests/'

    response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix)

    if 'Contents' in response:
        for item in response['Contents']:
            print(item['Key'])
    else:
        print("No objects found")

    playwright_manager = await setup_playwright()
    live_browser_url = await playwright_manager.get_live_browser_url()
    session_id = playwright_manager.get_session_id()
    print(live_browser_url)
    print(session_id)

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
        s3_path="s3://loggia-tests/loggia-test/tests/1/flow.json",
        elements_filter=elements_filter
    )

    response = await agent.send_prompt(plan)  # Added await here
    print(response)

    # Close the playwright_manager when done
    await playwright_manager.close()  # Added await here

if __name__ == "__main__":
    asyncio.run(main())