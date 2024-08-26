from litellm import completion
from litewebagent.agents.FunctionCallingAgents.BaseAgent import BaseAgent
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
from litewebagent.utils.functions import build_highlevel_action_parser
from litewebagent.utils.utils import *
import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict

logger = logging.getLogger(__name__)

# very basic chain of thought by providing the message list to OpenAI API
openai_client = OpenAI()

class FunctionCallingSearchAgent:
    def send_prompt(self, plan: str) -> Dict:
        if plan is not None:
            self.messages.append({"role": "user", "content": "The plan is: {}".format(plan)})
        return self.send_completion_request(plan, 0)
    def __init__(self, model_name, tools, available_tools, messages, goal, playwright_manager):
        self.model_name = model_name
        self.tools = tools
        self.available_tools = available_tools
        self.messages = messages
        self.goal = goal
        self.playwright_manager = playwright_manager
        self.messages.append({"role": "user", "content": "The goal is:{}".format(self.goal)})

    def make_plan(self):
        messages = [{"role": "system",
                     "content": "You are are helpful assistant to make a plan for a task or user request. Please provide a plan in the next few sentences."}]
        messages.append({"role": "assistant", "content": "The goal is{}".format(self.goal)})
        chat_completion = client.chat.completions.create(
            model=self.model_name, messages=messages,
        )
        plan = chat_completion.choices[0].message.content
        return plan
    def send_completion_request(self, plan: str, depth: int = 0) -> Dict:
        if plan is None and depth == 0:
            plan = self.make_plan()
        if depth >= 8:
            return None


        ### keep track of trajectory
        ### axtree and screenshots


        ### alternatively, just "function name" and "task descriptions"

        # import pdb; pdb.set_trace()
        # import pdb; pdb.set_trace()

        if not self.tools:
            response = completion(model=self.model_name, messages=self.messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        # assume just top 20
        response = completion(model=self.model_name, messages=self.messages, tools=self.tools, tool_choice="auto", n=20)
        import pdb; pdb.set_trace()
        # # [ChatCompletionMessageToolCall(function=Function(arguments='{"task_description":"search dining table"}', name='navigation')
        # # check whether name is the same, check whether task description is the same?
        # # response -> code
        # # {action: a, prob: 0.8}, {action: b, prob:0.2}, generate code
        # # take_action(task_description, action)
        #
        # import pdb; pdb.set_trace()
        #
        # logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
        #             str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        # logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
        #
        # if hasattr(response.choices[0].message, 'tool_calls'):
        #     tool_calls = response.choices[0].message.tool_calls
        # else:
        #     message = response.choices[0].message.model_dump()
        #     self.messages.append(message)
        #     return response
        #
        # if tool_calls is None or len(tool_calls) == 0:
        #     message = response.choices[0].message.model_dump()
        #     self.messages.append(message)
        #     return response
        #
        # tool_call_message = {"content": response.choices[0].message.content,
        #                      "role": response.choices[0].message.role,
        #                      "tool_calls": tool_calls}
        #
        # self.messages.append(tool_call_message)
        # tool_responses = self.process_tool_calls(tool_calls)
        # self.messages.extend(tool_responses)

        return self.send_completion_request(plan, depth + 1)