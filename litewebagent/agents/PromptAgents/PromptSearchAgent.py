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
from litewebagent.utils.playwright_manager import PlaywrightManager
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str
from litewebagent.utils.utils import build_highlevel_action_parser
from litewebagent.utils.utils import *
import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict
from collections import deque
from litewebagent.utils.utils import search_interactive_elements
from litewebagent.utils.replay import take_action
from litewebagent.utils.prompt_functions import extract_top_actions, is_goal_finished

logger = logging.getLogger(__name__)
openai_client = OpenAI()

class PromptSearchAgent:
    def send_prompt(self, plan: str) -> Dict:
        self.bfs()
        # TODO: select best trajectory from all trajectories,
        # TODO: better early stopping
        # TODO: plan VS goal
        return self.trajectories

    def __init__(self, model_name, tools, available_tools, messages, goal, playwright_manager):
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
        self.trajectories = []


    def get_next_actions(self, trajectory):
        print(trajectory)
        print("XXXXXXXXXXXXXXXXXX")
        self.playwright_manager.close()
        self.playwright_manager = PlaywrightManager(storage_state=None)
        self.playwright_manager.initialize()
        browser = self.playwright_manager.get_browser()
        context = self.playwright_manager.get_context()
        context = self.playwright_manager.get_context()
        page = self.playwright_manager.get_page()

        page = self.playwright_manager.get_page()
        self.playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
        starting_url = "https://www.google.com"
        page.goto(starting_url)

        try:
            for item in trajectory:
                steps = item['steps']
                for step in steps:
                    action, _ = take_action(step, self.playwright_manager, False)
        except Exception as e:
            return False, None


        time.sleep(3)
        page_info = extract_page_info(page)
        base64_image = encode_image(page_info['screenshot'])
        branching_factor = 2

        messages = [{"role": "system", "content": "The goal is {}, Is the overall goal finished?".format(self.goal)}]
        for item in trajectory:
            action = item['action']
            messages.append({"role": "user", "content": 'action is: {}'.format(action)})


        goal_finished = is_goal_finished(messages, openai_client)

        if goal_finished == False:
            updated_actions = extract_top_actions(trajectory, self.goal, page_info, self.action_set, openai_client, branching_factor)
            # Prepare messages for AI model

            return False, updated_actions
        else:
            return True, None


    def bfs(self):
        queue = deque([([], 0)])  # Initialize the queue with an empty trajectory and depth 0
        while queue:
            trajectory, depth = queue.popleft()  # Dequeue the first element
            goal_finished, next_actions = self.get_next_actions(trajectory)
            if depth < 3:
                self.trajectories.append({'goal_finished': goal_finished, 'trajectory': trajectory})
                if not goal_finished:
                    for action in next_actions:
                        print(action)
                        # Enqueue the new trajectory and increase the depth by 1
                        page = self.playwright_manager.get_page()
                        page_info = extract_page_info(page)
                        code, function_calls = self.action_set.to_python_code(action['action'])
                        steps = []
                        if len(function_calls) == 1:
                            try:
                                for function_name, function_args in function_calls:
                                    print(function_name, function_args)
                                    extracted_number = parse_function_args(function_args)
                                    # TODO: fix the cases where there is no element
                                    # scroll [0, 200]
                                    # None
                                    # An error occurred: 'NoneType' object does not support item assignment
                                    result = search_interactive_elements(page_info["interactive_elements"], extracted_number)
                                    print(result)
                                    result['action'] = action['action']
                                    result["url"] = page.url
                                    steps.append(result)
                                action['steps'] = steps
                                queue.append((trajectory + [action], depth + 1))
                                print(queue)
                            except Exception as e:
                                print(f"An error occurred: {e}")  # Provide more detailed error information


    def dfs(self, plan):
        pass