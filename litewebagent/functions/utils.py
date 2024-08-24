import base64
import json
import time
import os
import json
import logging
from openai import OpenAI
from litewebagent.observation.observation import (
    _pre_extract, _post_extract, extract_screenshot, extract_dom_snapshot,
    extract_dom_extra_properties, extract_merged_axtree, extract_focused_element_bid
)
from litewebagent.observation.extract_elements import extract_interactive_elements, highlight_elements, remove_highlights
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.playwright_manager import get_context, get_page
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str

logger = logging.getLogger(__name__)
openai_client = OpenAI()


def flatten_interactive_elements_to_str(
    interactive_elements,
    indent_char="\t"
):
    """
    Formats a list of interactive elements into a string, including only text, type, and bid.
    Skips elements where the type is 'html'.

    :param interactive_elements: List of dictionaries containing interactive element data
    :param indent_char: Character used for indentation (default: tab)
    :return: Formatted string representation of interactive elements
    """

    def format_element(element):
        # Skip if element type is 'html'
        if element.get('type', '').lower() == 'html' or element.get('type', '').lower() == 'body':
            return None

        # Add bid if present
        bid = f"[{element['bid']}] " if 'bid' in element else ""

        # Basic element info
        element_type = element.get('type', 'Unknown')
        text = element.get('text', '').replace('\n', ' ')

        return f"{bid}{element_type} {repr(text)}"

    formatted_elements = [
        formatted_elem for elem in interactive_elements
        if elem.get('include', True)
        for formatted_elem in [format_element(elem)]
        if formatted_elem is not None
    ]
    return "\n".join(formatted_elements)


def prepare_prompt(page_info, action_set, features):
    logger.info("features used: {}".format(features))
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
        {flatten_interactive_elements_to_str(page_info.get('interactive_elements', ''))}
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
    return prompt


def extract_page_info(page):
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


def query_openai_model(system_msg, prompt, screenshot_path, num_outputs):
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
        n=num_outputs
    )
    if num_outputs > 1:
        answer: list[str] = [x.message.content for x in response.choices]
    else:
        answer: list[str] = [response.choices[0].message.content]
    return answer


def execute_action(action, action_set, page, context, task_description, interactive_elements):
    code, function_calls = action_set.to_python_code(action)
    for function_name, function_args in function_calls:
        print(function_name, function_args)
        extracted_number = parse_function_args(function_args)
        result = search_interactive_elements(interactive_elements, extracted_number)
        print(result)
        result['action'] = action
        result["url"] = page.url
        result['task_description'] = task_description
        file_path = os.path.join('litewebagent', 'flow', 'steps.json')
        append_to_steps_json(result, file_path)

    logger.info("Executing action script")
    remove_highlights(page)
    execute_python_code(
        code,
        page,
        context,
        send_message_to_user=None,
        report_infeasible_instructions=None,
    )
    return result


def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


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


def parse_function_args(function_args):
    if not function_args or not isinstance(function_args, list):
        return None
    first_arg = function_args[0]
    return first_arg if isinstance(first_arg, str) and first_arg.replace('.', '', 1).isdigit() else None


def append_to_steps_json(result, file_path):
    json_line = json.dumps(result)
    with open(file_path, 'a') as file:
        file.write(json_line + '\n')
    print(f"Appended result to {file_path}")
