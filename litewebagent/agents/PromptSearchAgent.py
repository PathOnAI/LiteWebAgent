from litellm import completion
from .BaseAgent import BaseAgent
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
from litewebagent.playwright_manager import PlaywrightManager
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str
from litewebagent.functions.functions import build_highlevel_action_parser
from litewebagent.functions.utils import *
import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict
from collections import deque
from litewebagent.functions.utils import search_interactive_elements
from litewebagent.replay import take_action

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
        from pydantic import BaseModel

        class Plan(BaseModel):
            goal_finished: bool


        new_response = openai_client.beta.chat.completions.parse(
            model='gpt-4o-mini',
            messages=messages,
            response_format=Plan,
        )
        message = new_response.choices[0].message.parsed

        goal_finished = message.goal_finished

        if goal_finished == False:

            # Prepare messages for AI model
            system_msg = f"""
                    # Instructions
                    Review the current state of the page and all other information to find the best
                    possible next action to accomplish your goal. Your answer will be interpreted
                    and executed by a program, make sure to follow the formatting instructions.
    
                    Previous actions and action results are: {trajectory}
    
                    Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
                    # Goal:
                    {self.goal}"""
            prompt = prepare_prompt(page_info, self.action_set, 'axtree')

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user",
                     "content": [
                         {"type": "text", "text": prompt},
                         {"type": "image_url",
                          "image_url": {
                              "url": f"data:image/jpeg;base64,{base64_image}",
                              "detail": "high"
                          }
                          }
                     ]
                     },
                ],
                n=max(branching_factor * 2, 20)
            )
            responses: list[str] = [x.message.content for x in response.choices]
            highlevel_action_parser = build_highlevel_action_parser()
            print(responses)
            parsed_actions_count = defaultdict(int)
            all_actions = {}
            for response in responses:
                result = highlevel_action_parser.parse_string(response)
                result = result[0] if result else ""  # Convert to string
                if result not in all_actions:
                    all_actions[result] = {'action': response}
                parsed_actions_count[result] += 1
            print(parsed_actions_count)
            top_actions = sorted(parsed_actions_count, key=parsed_actions_count.get, reverse=True)[:branching_factor]
            top_action_count = sum([parsed_actions_count[action] for action in top_actions])
            updated_actions = []
            for action in top_actions:
                a = all_actions[action]
                a['prob'] = parsed_actions_count[action] / top_action_count
                updated_actions.append(a)
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