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
        page_info = extract_page_info(page, features)

        # Prepare messages for AI model
        system_msg, prompt = prepare_messages(goal, page_info, action_set, features)

        # Query OpenAI model
        action = query_openai_model(system_msg, prompt, page_info['screenshot'])

        # Execute the action
        result = execute_action(action, action_set, page, context, goal, page_info['interactive_elements'])

        # Capture post-action feedback
        feedback = capture_post_action_feedback(page, action, goal)

        return f"The action is: {action} - the result is: {feedback}"

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Task failed: {error_msg}")
        return f"Task failed: {error_msg}"


def extract_page_info(page, features):
    page_info = {}
    _pre_extract(page)
    screenshot_path = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_pre.png')
    page.screenshot(path=screenshot_path)
    page_info['screenshot'] = screenshot_path
    page_info['dom'] = extract_dom_snapshot(page)
    page_info['axtree'] = extract_merged_axtree(page)
    page_info['focused_element'] = extract_focused_element_bid(page)
    page_info['extra_properties'] = extract_dom_extra_properties(page_info.get('dom'))
    page_info['interactive_elements'] = extract_interactive_elements(page)
    highlight_elements(page, page_info['interactive_elements'])
    _post_extract(page)
    return page_info


def prepare_messages(goal, page_info, action_set, features):
    system_msg = f"""
    # Instructions
    Review the current state of the page and all other information to find the best
    possible next action to accomplish your goal. Your answer will be interpreted
    and executed by a program, make sure to follow the formatting instructions.

    Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
    # Goal:
    {goal}"""

    prompt = f"""
    """
    if "axtree" in features:
        prompt += f"""
        # Current Accessibility Tree:
        {flatten_axtree_to_str(page_info.get('axtree', ''))}
        """
    
    # TODO: flatten interactive elements
    if "interactive_elements" in features:
        prompt += f"""
        # Interactive elements:
        {page_info.get('interactive_elements', '')}
        """

    # TODO: clean dom elements
    if "dom" in features:
        prompt += f"""
        # Current DOM:
        {flatten_dom_to_str(page_info.get('dom', ''))}
        """

    prompt += f"""
        # Action Space
        {action_set.describe(with_long_description=False, with_examples=True)}
    
        # Screenshot
        The image provided is a screenshot of the current application state, corresponding to the Accessibility Tree above.
    
        Here is an example with chain of thought of a valid action when clicking on a button:
        "
        In order to accomplish my goal I need to click on the button with bid 12
        ```click('12')```
        "
    
        Please analyze the screenshot and the Accessibility Tree to determine the next appropriate action. Refer to visual elements from the screenshot if relevant to your decision.
        Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
        """
    return system_msg, prompt


def query_openai_model(system_msg, prompt, screenshot_path):
    base64_image = encode_image(screenshot_path)
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
    )
    return response.choices[0].message.content


def execute_action(action, action_set, page, context, goal, interactive_elements):
    try:
        code, function_calls = action_set.to_python_code(action)
        for function_name, function_args in function_calls:
            print(function_name, function_args)
            extracted_number = parse_function_args(function_args)

        result = search_interactive_elements(interactive_elements, extracted_number)
        print(result)
        result['action'] = action
        result["url"] = page.url
        result['goal'] = goal
        file_path = os.path.join('litewebagent', 'flow', 'steps.json')
        append_to_steps_json(result, file_path)

        logger.info("Executing action script")
        execute_python_code(
            code,
            page,
            context,
            send_message_to_user=None,
            report_infeasible_instructions=None,
        )
        return result
    except Exception as e:
        last_action_error = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Action execution failed: {last_action_error}")
        return f"Task failed with action error: {last_action_error}"


def capture_post_action_feedback(page, action, goal):
    screenshot_path_post = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_post.png')
    time.sleep(3)
    page.screenshot(path=screenshot_path_post)
    base64_image = encode_image(screenshot_path_post)
    prompt = f"""
    After we take action {action}, a screenshot was captured.

    # Screenshot description:
    The image provided is a screenshot of the application state after the action was performed.

    # The original goal:
    {goal}

    Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
    """

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
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
    )

    return response.choices[0].message.content


def search_interactive_elements(interactive_elements, extracted_number):
    for element in interactive_elements:
        if element.get('bid') == extracted_number:
            return {
                'text': element.get('text'),
                'type': element.get('type'),
                'tag': element.get('tag'),
                'id': element.get('id'),
                'href': element.get('href'),
                'title': element.get('title')
            }
    return None  # Return None if no matching element is found


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

# Add any additional helper functions here