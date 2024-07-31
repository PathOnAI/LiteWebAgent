from agent_creation.action.highlevel import HighLevelActionSet
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
from agent_creation.agent.base import AbstractAgentArgs, AgentInfo, Agent
import dataclasses
import logging
logger = logging.getLogger(__name__)
class DemoAgent(Agent):
    """A basic agent using OpenAI API, to demonstrate BrowserGym's functionalities."""

    action_set = HighLevelActionSet(
        #subsets=["chat", "bid"],  # define a subset of the action space
        subsets = ["chat", "infeas", "bid", "coord", "nav", "tab"],
        # subsets=["chat", "bid", "coord"] # allow the agent to also use x,y coordinates
        strict=False,  # less strict on the parsing of the actions
        multiaction=True,  # enable to agent to take multiple actions at once
        demo_mode="default",  # add visual effects
    )
    # use this instead to allow the agent to directly use Python code
    # action_set = PythonActionSet())

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

    def get_action(self, obs: dict) -> tuple[str, dict]:
        system_msg = f"""\
# Instructions
Review the current state of the page and all other information to find the best
possible next action to accomplish your goal. Your answer will be interpreted
and executed by a program, make sure to follow the formatting instructions.

# Goal:
{obs["goal"]}"""

        prompt = f"""\

# Current Accessibility Tree:
{obs["axtree_txt"]}

# Last action:
{obs["last_action"]}

# Last action error:
{obs["last_action_error"]}

# Action Space
{self.action_set.describe(with_long_description=False, with_examples=True)}

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click("12")```
"
"""

        # query OpenAI model
        if obs["last_action"]:
            logger.debug(obs["last_action"])
        if obs["last_action_error"]:
            logger.debug(obs["last_action_error"])
        logger.debug(prompt)
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
        )
        action = response.choices[0].message.content

        return action, {}


@dataclasses.dataclass
class DemoAgentArgs(AbstractAgentArgs):
    """
    This class is meant to store the arguments that define the agent.

    By isolating them in a dataclass, this ensures serialization without storing
    internal states of the agent.
    """

    model_name: str = "gpt-4o-mini"

    def make_agent(self):
        return DemoAgent(model_name=self.model_name)