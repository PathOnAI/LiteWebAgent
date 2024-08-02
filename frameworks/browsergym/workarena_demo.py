"""
browsergym                               0.4.0
browsergym-core                          0.4.0
browsergym-experiments                   0.4.0
browsergym-miniwob                       0.4.0
browsergym-visualwebarena                0.4.0
browsergym-webarena                      0.4.0
browsergym-workarena                     0.3.1
"""

# import gymnasium as gym
# import browsergym.workarena
#
# env = gym.make('browsergym/workarena.servicenow.filter-asset-list',
#                headless=False)
# obs, info = env.reset()
# done = False
#
# while not done:
#     action = "noop()"
#     obs, reward, terminated, truncated, info = env.step(action)
#     print(f"Reward: {reward}, Done: {done}, Info: {info}")
#
# env.close()

import gymnasium as gym
import browsergym.core  # register the openended task as a gym environment
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.core.action.python import PythonActionSet
from browsergym.utils.obs import flatten_axtree_to_str
from browsergym.core.chat import Chat
import gymnasium as gym
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image
import logging
from logging.handlers import RotatingFileHandler
import dataclasses
from dotenv import load_dotenv
_ = load_dotenv()


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)

#@dataclass
# class EnvArgs:
#     task_name: str
#     task_seed: int = None
#     max_steps: int = None
#     headless: bool = True
#     wait_for_user_message: bool = False
#     task_kwargs: dict = None
#
#     def make_env(self, action_mapping):
#         return gym.make(
#             "browsergym/workarena.servicenow.filter-asset-list",
#             disable_env_checker=True,
#             max_episode_steps=self.max_steps,
#             headless=self.headless,
#             wait_for_user_message=self.wait_for_user_message,
#             action_mapping=action_mapping,
#             task_kwargs=self.task_kwargs
#         )

@dataclass
class StepInfo:
    step: int = 0
    obs: dict = None
    reward: float = 0
    terminated: bool = False
    truncated: bool = False
    action: str = None
    agent_info: dict = field(default_factory=dict)

    def from_step(self, env: gym.Env, action: str, obs_preprocessor: callable = None):
        self.obs, self.reward, self.terminated, self.truncated, _ = env.step(action)
        if obs_preprocessor:
            self.obs = obs_preprocessor(self.obs)

    def from_action(self, agent):
        self.action, self.agent_info = agent.get_action(self.obs.copy())
        return self.action

    def from_reset(self, env: gym.Env, seed: int, obs_preprocessor: callable = None):
        self.obs, _ = env.reset(seed=seed)
        self.reward, self.terminated, self.truncated = 0, False, False
        if obs_preprocessor:
            self.obs = obs_preprocessor(self.obs)
        return self.obs

    @property
    def is_done(self):
        return self.terminated or self.truncated

def get_screenshot(obs):
    if 'screenshot' in obs:
        return Image.fromarray(obs['screenshot'])
    return None

def _send_chat_info(chat: Chat, action: str, agent_info: dict):
    """Send the think and action info to the chat."""
    msg = ""
    if "think" in agent_info:
        msg += f"""\
{agent_info["think"]}

"""

    msg += f"""\
action:
{action}
"""

    chat.add_message(role="info", msg=msg)


# env_args = EnvArgs(
#     task_name='workarena.servicenow.filter-asset-list',
#     headless=False,
#     wait_for_user_message=True
# )


import dataclasses
from dotenv import load_dotenv
_ = load_dotenv()
from browsergym.experiments import Agent, AbstractAgentArgs
from browsergym.core.action.highlevel import HighLevelActionSet
from browsergym.core.action.python import PythonActionSet
from browsergym.utils.obs import flatten_axtree_to_str


class DemoAgent(Agent):
    """A basic agent using OpenAI API, to demonstrate BrowserGym's functionalities."""

    action_set = HighLevelActionSet(
        subsets=["chat", "bid"],  # define a subset of the action space
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

# Action Space
{self.action_set.describe(with_long_description=False, with_examples=True)}

Here is an example with chain of thought of a valid action when clicking on a button:
"
In order to accomplish my goal I need to click on the button with bid 12
```click("12")```
"
"""

        # query OpenAI model
        print(system_msg)
        print(prompt)
        response = self.openai_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": prompt},
            ],
        )
        action = response.choices[0].message.content
        # import pdb; pdb.set_trace()

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


agent_args = DemoAgentArgs(model_name="gpt-4o-mini")
demo_agent = agent_args.make_agent()
import browsergym.workarena
#env = env_args.make_env(action_mapping=demo_agent.action_set.to_python_code)  # Replace None with your action mapping if needed

#.filter-asset-list
env = gym.make('browsergym/workarena.servicenow.create-user', headless=False, wait_for_user_message=True, action_mapping=demo_agent.action_set.to_python_code)

step_info = StepInfo()

obs = step_info.from_reset(env, 42, demo_agent.obs_preprocessor)
print("Initial observation:", obs)
# import pdb; pdb.set_trace()

while not step_info.is_done:
    # Get action from the agent
    action = step_info.from_action(demo_agent)
    logger.debug(f'Before taking action: {action}')

    # Send chat info
    _send_chat_info(env.unwrapped.chat, action, step_info.agent_info)

    # Take a step in the environment
    step_info.from_step(env, action, demo_agent.obs_preprocessor)
    logger.debug('After taking action')
    logger.debug(f'Observation: {step_info.obs}')
    logger.debug(f'Reward: {step_info.reward}')
    logger.debug(f'Done: {step_info.is_done}')

    # Save screenshot if available
    screenshot = get_screenshot(step_info.obs)
    if screenshot:
        screenshot.save(f"screenshot_step_{step_info.step}.jpg")

    step_info.step += 1

env.close()