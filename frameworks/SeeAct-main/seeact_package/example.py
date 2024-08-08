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
    agent = SeeActAgent(model="gpt-4o")
    await agent.start()
    while not agent.complete_flag:
        prediction_dict = await agent.predict()
        await agent.execute(prediction_dict)
    await agent.stop()

if __name__ == "__main__":
    asyncio.run(run_agent())
