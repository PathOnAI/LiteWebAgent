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
from litewebagent.utils.utils import *

logger = logging.getLogger(__name__)
openai_client = OpenAI()





def get_action_probability(responses, branching_factor):
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

    print(updated_actions)
    return updated_actions

def take_action(task_description, agent_type, features=None, branching_factor=None, playwright_manager=None):
    try:
        context = playwright_manager.get_context()
        page = playwright_manager.get_page()
        action_set = HighLevelActionSet(
            subsets=agent_type,
            strict=False,
            multiaction=True,
            demo_mode="default"
        )

        # Extract page information
        time.sleep(3)
        page_info = extract_page_info(page)

        # Prepare messages for AI model
        system_msg = f"""
        # Instructions
        Review the current state of the page and all other information to find the best
        possible next action to accomplish your goal. Your answer will be interpreted
        and executed by a program, make sure to follow the formatting instructions.

        Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
        # Goal:
        {task_description}"""
        prompt = prepare_prompt(page_info, action_set, features)

        # Query OpenAI model
        if branching_factor == None:
            responses = query_openai_model(system_msg, prompt, page_info['screenshot'], num_outputs=20)
        else:
            responses = query_openai_model(system_msg, prompt, page_info['screenshot'], num_outputs=max(branching_factor * 2, 20))
        updated_actions = get_action_probability(responses, branching_factor)
        action = updated_actions[0]['action']

        # Execute the action
        try:
            execute_action(action, action_set, page, context, task_description, page_info['interactive_elements'])
        except Exception as e:
            last_action_error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Action execution failed: {last_action_error}")
            return f"Task failed with action error: {last_action_error}"

        # Capture post-action feedback
        feedback = capture_post_action_feedback(page, action, task_description)

        return f"The action is: {action} - the result is: {feedback}"

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Task failed: {error_msg}")
        return f"Task failed: {error_msg}"


def navigation(task_description, features=None, branching_factor=None, playwright_manager= None):
    response = take_action(task_description, ["bid", "nav"], features, branching_factor, playwright_manager)
    return response


def upload_file(task_description, features=None, branching_factor=None, playwright_manager=None):
    response = take_action(task_description, ["file"], features, branching_factor, playwright_manager)
    return response


def select_option(task_description, features=None, branching_factor=None, playwright_manager=None):
    response = take_action(task_description, ["select_option"], features, branching_factor, playwright_manager)
    return response
