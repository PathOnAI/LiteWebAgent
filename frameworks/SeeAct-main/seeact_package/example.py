import asyncio
import os
from seeact.agent import SeeActAgent

# Setup your API Key here, or pass through environment
# os.environ["OPENAI_API_KEY"] = "Your API KEY Here"
# os.environ["GEMINI_API_KEY"] = "Your API KEY Here"

from dotenv import load_dotenv
# from openai import OpenAI
# from litellm import completion
import os
_ = load_dotenv()

async def run_agent():
    # default_task="search on airbnb, destination SF, check in 8/15, check out 8/20",
    #                         default_website="https://www.airbnb.com/",
    agent = SeeActAgent(model="gpt-4o", grounding_strategy="text_choice")
    await agent.start()
    while not agent.complete_flag:
        prediction_dict = await agent.predict()
        await agent.execute(prediction_dict)
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(run_agent())
