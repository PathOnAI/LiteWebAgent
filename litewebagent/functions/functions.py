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
from litewebagent.playwright_manager import get_context, get_page
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str
from .utils import *

logger = logging.getLogger(__name__)
openai_client = OpenAI()


def take_action(goal, agent_type, features=None):
    try:
        context = get_context()
        page = get_page()
        action_set = HighLevelActionSet(
            subsets=agent_type,
            strict=False,
            multiaction=True,
            demo_mode="default"
        )

        # Extract page information
        page_info = extract_page_info(page)

        # Prepare messages for AI model
        system_msg = f"""
        # Instructions
        Review the current state of the page and all other information to find the best
        possible next action to accomplish your goal. Your answer will be interpreted
        and executed by a program, make sure to follow the formatting instructions.

        Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
        # Goal:
        {goal}"""
        prompt = prepare_prompt(page_info, action_set, features)

        # Query OpenAI model
        action = query_openai_model(system_msg, prompt, page_info['screenshot'])

        # Execute the action
        try:
            execute_action(action, action_set, page, context, goal, page_info['interactive_elements'])
        except Exception as e:
            last_action_error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Action execution failed: {last_action_error}")
            return f"Task failed with action error: {last_action_error}"

        # Capture post-action feedback
        feedback = capture_post_action_feedback(page, action, goal)

        return f"The action is: {action} - the result is: {feedback}"

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Task failed: {error_msg}")
        return f"Task failed: {error_msg}"


def navigation(goal, features=None):
    response = take_action(goal, ["bid", "nav"], features)
    return response


def upload_file(goal, features=None):
    response = take_action(goal, ["file"], features)
    return response


def scan_page_extract_information(instruction):
    page = get_page()
    time.sleep(2)
    page.screenshot(path='./playground/gpt4v/screenshot.png', full_page=True)
    html_content = page.content()
    main_content = page.evaluate('''() => {
        // ... (keep the existing JavaScript code for extracting main content)
    }''')
    with open('./playground/gpt4v/main_content.html', 'w') as f:
        f.write(main_content)

    image_path = './playground/gpt4v/screenshot.png'
    image_data_url = local_image_to_data_url(image_path)

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": instruction},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": image_data_url
                        }
                    },
                ]
            }
        ]
    )

    content = response.choices[0].message.content
    return f"Scanned the page content according to your instruction {instruction}. Here's the answer:\n\n{content}"
