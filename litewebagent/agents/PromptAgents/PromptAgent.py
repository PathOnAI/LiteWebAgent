from litellm import completion
from typing import List, Dict, Any
import json
import logging
import time
import os
import json
import logging
from openai import OpenAI
from litewebagent.observation.observation import (
    _pre_extract, _post_extract, extract_screenshot, extract_dom_snapshot,
    extract_dom_extra_properties, extract_merged_axtree, extract_focused_element_bid
)
from litewebagent.observation.extract_elements import extract_interactive_elements, highlight_elements
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str
from litewebagent.utils.utils import build_highlevel_action_parser
from litewebagent.utils.utils import *
import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict
from collections import deque
from litewebagent.utils.utils import *
from litewebagent.utils.prompt_functions import extract_top_actions, is_goal_finished

logger = logging.getLogger(__name__)

# very basic chain of thought by providing the message list to OpenAI API
openai_client = OpenAI()



class PromptAgent:


    def send_prompt(self, plan: str) -> Dict:
        if plan is not None:
            self.messages.append({"role": "user", "content": "The plan is: {}".format(plan)})
        trajectory = self.send_completion_request(plan, 0, [])
        messages = [{"role": "system", "content": "The goal is {}, summarize the actions and result taken by the web agent in one sentence, be concise.".format(self.goal)}]
        for item in trajectory:
            action = item['action']
            action_result = item['action_result']
            messages.append({"role": "user", "content": 'action is: {}'.format(action)})
            messages.append({"role": "user", "content": 'action result is: {}'.format(action_result)})
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
        )
        summary = response.choices[0].message.content
        return summary

    def __init__(self, model_name, tools, available_tools, messages, goal, playwright_manager, log_folder):
        self.model_name = model_name
        self.tools = tools
        self.available_tools = available_tools
        self.messages = messages
        self.goal = goal
        self.playwright_manager = playwright_manager
        self.messages.append({"role": "user", "content": "The goal is:{}".format(self.goal)})
        self.agent_type = ["bid", "nav", "file", "select_option"]
        self.action_set = HighLevelActionSet(
            subsets=self.agent_type,
            strict=False,
            multiaction=True,
            demo_mode="default"
        )
        self.log_folder = log_folder


    def send_completion_request(self, plan: str, depth: int = 0, trajectory= []) -> Dict:
        if depth >= 8:
            return None

        context = self.playwright_manager.get_context()
        page = self.playwright_manager.get_page()
        # Extract page information
        time.sleep(3)
        page_info = extract_page_info(page, self.log_folder)
        branching_factor = 5
        updated_actions = extract_top_actions(trajectory, self.goal, page_info, self.action_set, openai_client,
                                              branching_factor)
        next_action = updated_actions[0]['action']
        execute_action(next_action, self.action_set, page, context, self.goal, page_info['interactive_elements'], self.log_folder)
        feedback = capture_post_action_feedback(page, next_action, self.goal, self.log_folder)
        trajectory.append({'action': next_action, 'action_result': feedback})

        print(f"The action is: {next_action} - The action result is: {feedback}")

        messages = [{"role": "system", "content": "The goal is {}, Is the overall goal finished?".format(self.goal)}]
        for item in trajectory:
            action = item['action']
            action_result = item['action_result']
            messages.append({"role": "user", "content": 'action is: {}'.format(action)})
            messages.append({"role": "user", "content": 'action result is: {}'.format(action_result)})

        goal_finished = is_goal_finished(messages, openai_client)

        if goal_finished:
            return trajectory

        return self.send_completion_request(plan, depth + 1, trajectory)