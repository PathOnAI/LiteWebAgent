## placeholder

from litellm import completion
from .BaseAgent import BaseAgent
from typing import List, Dict, Any
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError
import os
import random
import math

_ = load_dotenv()

openai_client = OpenAI()

logger = logging.getLogger(__name__)

class MCTSNode:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.value = 0

    def add_child(self, child_state):
        child = MCTSNode(child_state, self)
        self.children.append(child)
        return child

    def update(self, result):
        self.visits += 1
        self.value += result

    def fully_expanded(self):
        return len(self.children) > 0

    def best_child(self, c_param=1.4):
        choices_weights = [
            (c.value / c.visits) + c_param * math.sqrt((2 * math.log(self.visits) / c.visits))
            for c in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

class MCTS:
    def __init__(self, root_state, simulate_fn, expand_fn, is_terminal_fn, max_iterations=100):
        self.root = MCTSNode(root_state)
        self.simulate = simulate_fn
        self.expand = expand_fn
        self.is_terminal = is_terminal_fn
        self.max_iterations = max_iterations

    def search(self):
        for _ in range(self.max_iterations):
            node = self.select(self.root)
            if not self.is_terminal(node.state):
                node = self.expand(node)
            result = self.simulate(node.state)
            self.backpropagate(node, result)
        return self.best_action(self.root)

    def select(self, node):
        while not self.is_terminal(node.state):
            if not node.fully_expanded():
                return node
            node = node.best_child()
        return node

    def backpropagate(self, node, result):
        while node is not None:
            node.update(result)
            node = node.parent

    def best_action(self, node):
        return max(node.children, key=lambda c: c.visits).state

class MCTSAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.mcts = MCTS(
            root_state=self.make_plan(),
            simulate_fn=self.simulate_plan,
            expand_fn=self.expand_plan,
            is_terminal_fn=self.is_plan_terminal,
            max_iterations=100
        )

    def make_plan(self):
        # Initial plan creation logic
        return "Initial high-level plan"

    def simulate_plan(self, plan):
        # Simulation logic: estimate the value of a plan
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Evaluate the following plan for achieving the goal: " + self.goal},
                {"role": "user", "content": plan}
            ]
        )
        # Extract a numerical score from the response
        # This is a simplification; you might want to implement a more sophisticated scoring system
        score = len(response.choices[0].message.content) / 100  # Example scoring
        return score

    def expand_plan(self, node):
        # Expansion logic: generate possible next steps for a plan
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generate a possible next step for the following plan to achieve the goal: " + self.goal},
                {"role": "user", "content": node.state}
            ]
        )
        new_plan = node.state + "\n" + response.choices[0].message.content
        return node.add_child(new_plan)

    def is_plan_terminal(self, plan):
        # Terminal state check: determine if a plan is complete
        response = openai_client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Is the following plan complete for achieving the goal: " + self.goal},
                {"role": "user", "content": plan}
            ]
        )
        return "yes" in response.choices[0].message.content.lower()

    def send_completion_request(self, plan: str = None, depth: int = 0) -> Dict:
        if plan is None and depth == 0:
            plan = self.mcts.search()  # Use MCTS to generate the plan

        if depth >= 8:
            return None

        if not self.tools:
            response = completion(model=self.model_name, messages=self.messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        logger.info("last message: %s", json.dumps(self.messages[-1]))
        logger.info('current plan: %s', plan)

        if depth > 0:
            from pydantic import BaseModel
            class Plan(BaseModel):
                goal_finished: bool

            prompt = """
            Goal: {}
            Current plan: {}

            Based on the progress made so far, please provide:

            1. An updated complete plan
            2. A list of tasks that have already been completed
            3. An explanation of changes and their rationale

            Format your response as follows:

            Updated Plan:
            - [Step 1]
            - [Step 2]
            - ...

            Completed Tasks:
            - [Task 1]
            - [Task 2]
            - ...
            """.format(self.goal, plan)
            self.messages.append({"role": "user", "content": prompt})
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=self.messages
            )
            plan = response.choices[0].message.content
            new_response = openai_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[{"role": "system", "content": "Is the overall goal finished?"}, {"role": "user", "content": plan}],
                response_format=Plan
            )
            message = new_response.choices[0].message.parsed
            goal_finished = message.goal_finished
            if goal_finished:
                logger.info("goal finished")
                return response
            else:
                self.messages.append({"role": "user", "content": plan})

        logger.info('updated plan: %s', plan)
        response = completion(model=self.model_name, messages=self.messages, tools=self.tools, tool_choice="auto")

        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)

        if hasattr(response.choices[0].message, 'tool_calls'):
            tool_calls = response.choices[0].message.tool_calls
        else:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        if tool_calls is None or len(tool_calls) == 0:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response
        # limit one function calling at a time
        tool_calls = [tool_calls[0]]

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        self.messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        self.messages.extend(tool_responses)

        return self.send_completion_request(plan, depth + 1)