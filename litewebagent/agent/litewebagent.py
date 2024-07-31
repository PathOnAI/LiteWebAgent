import asyncio
from playwright.sync_api import sync_playwright
from agent_creation.action.highlevel import HighLevelActionSet
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
from agent_creation.agent.base import AbstractAgentArgs, AgentInfo, Agent
import dataclasses
import logging
from agent_creation.action.functions import fill, click
from agent_creation.action.base import execute_python_code

logger = logging.getLogger(__name__)

class LiteWebAgent(Agent):
    def obs_preprocessor(self, obs: dict) -> dict:
        return {
            "goal": obs["goal"],
            "dom_txt":  flatten_dom_to_str(obs["dom_object"]),
            "last_action": obs["last_action"],
            "last_action_error": obs["last_action_error"],
            "axtree_txt": flatten_axtree_to_str(obs["axtree_object"]),
        }

    def __init__(self, model_name) -> None:
        super().__init__()
        self.model_name = model_name
        from openai import OpenAI
        self.openai_client = OpenAI()
        self.playwright = None
        self.browser = None
        self.page = None

    def initialize(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch()
        self.page = self.browser.new_page()

    def execute_python_code(self, code: str) -> str:
        try:
            exec_globals = {'page': self.page, 'browser': self.browser}
            exec(f"def __temp_func():\n{code}", exec_globals)
            result = exec_globals['__temp_func']()
            return str(result) if result is not None else ""
        except Exception as e:
            return f"Error executing code: {str(e)}"

    def get_action(self, obs: dict) -> tuple[str, dict]:
        return "no action", {}
#     async def get_action(self, obs: dict) -> tuple[str, dict]:
#         if self.page is None:
#             self.initialize()
#
#         # Generate Python code to navigate to amazon.com
#         python_code = """
# page.goto("https://www.amazon.com")
# return f"Current URL: {page.url}"
# """
#
#         # Execute the generated Python code
#         result = self.execute_python_code(python_code)
#
#         # Return the action and result
#         return "execute_python", {"code": python_code, "result": result}

    def cleanup(self):
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

@dataclasses.dataclass
class LiteWebAgentArgs(AbstractAgentArgs):
    model_name: str

    def make_agent(self) -> Agent:
        return LiteWebAgent(self.model_name)


@dataclasses.dataclass
class LiteWebAgentArgs(AbstractAgentArgs):
    """
    This class is meant to store the arguments that define the agent.

    By isolating them in a dataclass, this ensures serialization without storing
    internal states of the agent.
    """

    model_name: str = "gpt-4o-mini"

    def make_agent(self):
        return LiteWebAgent(model_name=self.model_name)