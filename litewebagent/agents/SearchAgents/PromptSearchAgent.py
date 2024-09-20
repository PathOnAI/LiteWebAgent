import json
import logging
import time
from collections import deque
from typing import Any, Dict, List

from openai import OpenAI

from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.utils.playwright_manager import PlaywrightManager
from litewebagent.utils.utils import (
    encode_image,
    extract_page_info,
    parse_function_args,
    search_interactive_elements,
)
from litewebagent.utils.evaluators import goal_finished_evaluator
from litewebagent.utils.replay import take_action
from litewebagent.utils.prompt_functions import extract_top_actions, is_goal_finished

logger = logging.getLogger(__name__)
openai_client = OpenAI()


class PromptSearchAgent:
    def __init__(
        self,
        starting_url: str,
        model_name: str,
        tools: List[str],
        available_tools: List[str],
        messages: List[Dict[str, Any]],
        goal: str,
        playwright_manager: PlaywrightManager,
    ):
        self.model_name = model_name
        self.starting_url = starting_url
        self.tools = tools
        self.available_tools = available_tools
        self.messages = messages
        self.goal = goal
        self.playwright_manager = playwright_manager
        self.messages.append({"role": "user", "content": f"The goal is: {self.goal}"})
        self.agent_type = ["bid", "nav", "file", "select_option"]
        self.action_set = HighLevelActionSet(
            subsets=self.agent_type, strict=False, multiaction=True, demo_mode="default"
        )
        self.trajectories = []

    def send_prompt(self, plan: str, search_algorithm: str = "bfs") -> List[Dict[str, Any]]:
        if search_algorithm == "bfs":
            logger.info("Starting BFS algorithm")
            self.bfs()
        else:
            logger.info("Starting DFS algorithm")
            self.dfs()
        return self.trajectories

    def get_next_actions(self, trajectory: List[Dict[str, Any]], finished_score_threshold: float = 0.9):
        logger.debug("Initializing Playwright Manager")
        self.playwright_manager.close()
        self.playwright_manager = PlaywrightManager(storage_state=None)
        self.playwright_manager.initialize()
        page = self.playwright_manager.get_page()
        self.playwright_manager.playwright.selectors.set_test_id_attribute("data-unique-test-id")
        page.goto(self.starting_url)

        try:
            for item in trajectory:
                steps = item["steps"]
                for step in steps:
                    take_action(step, self.playwright_manager, False)
        except Exception as e:
            logger.error(f"An error occurred during action execution: {e}")
            return False, None

        time.sleep(3)
        page_info = extract_page_info(page)
        branching_factor = 2

        messages = [
            {"role": "system", "content": f"The goal is {self.goal}, Is the overall goal finished?"}
        ]
        for item in trajectory:
            action = item["action"]
            messages.append({"role": "user", "content": f"Action is: {action}"})

        goal_finished, score = goal_finished_evaluator(messages, openai_client)

        if not goal_finished or score < finished_score_threshold:
            logger.info(f"Goal not finished or below threshold (Score: {score})")
            updated_actions = extract_top_actions(
                trajectory, self.goal, page_info, self.action_set, openai_client, branching_factor
            )
            return False, updated_actions
        else:
            logger.info("Goal finished successfully")
            return True, None

    def bfs(self):
        queue = deque([([], 0)])
        while queue:
            trajectory, depth = queue.popleft()
            goal_finished, next_actions = self.get_next_actions(trajectory)
            if depth < 3:
                self.trajectories.append({"goal_finished": goal_finished, "trajectory": trajectory})
                if not goal_finished and next_actions:
                    for action in next_actions:
                        page = self.playwright_manager.get_page()
                        page_info = extract_page_info(page)
                        code, function_calls = self.action_set.to_python_code(action["action"])
                        steps = []
                        if len(function_calls) == 1:
                            try:
                                for function_name, function_args in function_calls:
                                    extracted_number = parse_function_args(function_args)
                                    result = search_interactive_elements(
                                        page_info["interactive_elements"], extracted_number
                                    )
                                    result["action"] = action["action"]
                                    result["url"] = page.url
                                    steps.append(result)
                                action["steps"] = steps
                                queue.append((trajectory + [action], depth + 1))
                            except Exception as e:
                                logger.error(f"An error occurred: {e}")

    def dfs(self, trajectory: List[Dict[str, Any]] = None, depth: int = 0):
        if trajectory is None:
            trajectory = []
        goal_finished, next_actions = self.get_next_actions(trajectory)
        if depth < 3:
            self.trajectories.append({"goal_finished": goal_finished, "trajectory": trajectory})
            if not goal_finished and next_actions:
                for action in next_actions:
                    page = self.playwright_manager.get_page()
                    page_info = extract_page_info(page)
                    code, function_calls = self.action_set.to_python_code(action["action"])
                    steps = []
                    if len(function_calls) == 1:
                        try:
                            for function_name, function_args in function_calls:
                                extracted_number = parse_function_args(function_args)
                                result = search_interactive_elements(
                                    page_info["interactive_elements"], extracted_number
                                )
                                result["action"] = action["action"]
                                result["url"] = page.url
                                steps.append(result)
                            action["steps"] = steps
                            self.dfs(trajectory + [action], depth + 1)
                        except Exception as e:
                            logger.error(f"An error occurred: {e}")
