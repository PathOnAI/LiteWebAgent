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
# from litewebagent.playwright_manager import get_context, get_page
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str
from litewebagent.functions.functions import build_highlevel_action_parser
from litewebagent.functions.utils import *
import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict
from collections import deque
from litewebagent.functions.utils import *

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

    def __init__(self, model_name, tools, available_tools, messages, goal, playwright_manager):
        self.model_name = model_name
        self.tools = tools
        self.available_tools = available_tools
        self.messages = messages
        self.goal = goal
        self.playwright_manager = playwright_manager
        self.messages.append({"role": "user", "content": "The goal is:{}".format(self.goal)})


    def send_completion_request(self, plan: str, depth: int = 0, trajectory= []) -> Dict:
        if depth >= 8:
            return None

        context = self.playwright_manager.get_context()
        page = self.playwright_manager.get_page()
        agent_type = ["bid", "nav", "file", "select_option"]
        action_set = HighLevelActionSet(
            subsets=agent_type,
            strict=False,
            multiaction=True,
            demo_mode="default"
        )

        # Extract page information
        time.sleep(3)
        page_info = extract_page_info(page)
        branching_factor = 5

        # Prepare messages for AI model
        system_msg = f"""
                # Instructions
                Review the current state of the page and all other information to find the best
                possible next action to accomplish your goal. Your answer will be interpreted
                and executed by a program, make sure to follow the formatting instructions.
                
                Previous actions and action results are: {trajectory}

                Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
                # Goal:
                {plan}"""
        prompt = prepare_prompt(page_info, action_set, 'axtree')
        base64_image = encode_image(page_info['screenshot'])
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

        next_action = updated_actions[0]['action']
        execute_action(next_action, action_set, page, context, self.goal, page_info['interactive_elements'])
        feedback = capture_post_action_feedback(page, next_action, self.goal)
        trajectory.append({'action': next_action, 'action_result': feedback})

        print(f"The action is: {next_action} - The action result is: {feedback}")

        messages = [{"role": "system", "content": "The goal is {}, Is the overall goal finished?".format(self.goal)}]
        for item in trajectory:
            action = item['action']
            action_result = item['action_result']
            messages.append({"role": "user", "content": 'action is: {}'.format(action)})
            messages.append({"role": "user", "content": 'action result is: {}'.format(action_result)})
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
        if goal_finished:
            return trajectory

        return self.send_completion_request(plan, depth + 1, trajectory)