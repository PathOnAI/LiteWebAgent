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
from litewebagent.action.base import execute_python_code
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str

logger = logging.getLogger(__name__)
openai_client = OpenAI()


import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict

def setup_logger(log_folder, log_file="log.txt"):
    if not os.path.exists(log_folder):
        os.makedirs(log_folder)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(log_folder, log_file), mode="w"),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def build_highlevel_action_parser() -> pp.ParserElement:
    def make_keyword(kwd_str, kwd_value):
        return pp.Keyword(kwd_str).set_parse_action(pp.replace_with(kwd_value))

    TRUE = make_keyword("True", True)
    FALSE = make_keyword("False", False)
    NONE = make_keyword("None", None)

    LBRACK, RBRACK, LBRACE, RBRACE, LPAREN, RPAREN, COLON = map(pp.Suppress, "[]{}():")

    def literal_eval(toks):
        return ast.literal_eval(toks[0])

    string = pp.python_quoted_string().set_parse_action(literal_eval)
    number = pp.pyparsing_common.number()
    dict = pp.Forward().set_name("dict")
    list = pp.Forward().set_name("list")
    tuple = pp.Forward().set_name("tuple")
    element = (string | number | dict | list | tuple | TRUE | FALSE | NONE).set_name("element")

    list_items = pp.DelimitedList(element, allow_trailing_delim=True).set_name(None)
    list << pp.Group(LBRACK + pp.Optional(list_items) + RBRACK, aslist=True)
    tuple << pp.Group(LPAREN + pp.Optional(list_items) + RPAREN, aslist=True).set_parse_action(
        lambda tokens: tuple(tokens[0])
    )

    dict_item = pp.Group(string + COLON + element, aslist=True).set_name("dict item")
    dict_items = pp.DelimitedList(dict_item, allow_trailing_delim=True).set_name(None)
    dict << pp.Dict(LBRACE + pp.Optional(dict_items) + RBRACE, asdict=True)

    arg = element
    list_args = pp.DelimitedList(arg, allow_trailing_delim=True).set_name(None)
    named_arg = (pp.pyparsing_common.identifier() + pp.Literal("=").suppress() + element).set_parse_action(
        lambda tokens: f"{tokens[0]}={repr(tokens[1])}"
    )
    list_named_args = pp.DelimitedList(named_arg, allow_trailing_delim=True).set_name(None)

    def format_function_call(tokens):
        func_name = tokens[0]
        args = tokens[1] if len(tokens) > 1 else []
        formatted_args = [repr(arg) if isinstance(arg, str) else str(arg) for arg in args]
        return f"{func_name}({', '.join(formatted_args)})"

    function_call = (pp.pyparsing_common.identifier() +
                     pp.Group(LPAREN + pp.Optional(list_args) + pp.Optional(list_named_args) + RPAREN)
                     ).set_parse_action(format_function_call)

    # Allow any text before the function call
    text_before_call = pp.SkipTo(function_call).suppress()

    # Define a single function call that may have text before it
    flexible_function_call = text_before_call + function_call

    # Allow multiple function calls, each potentially preceded by text
    multiple_function_calls = pp.OneOrMore(flexible_function_call)
    multiple_function_calls.ignore(pp.python_style_comment())

    # Set parse action to join all parsed function calls into a single string
    parser = multiple_function_calls.set_parse_action(lambda t: ' '.join(t))

    return parser

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


def extract_page_info(page, log_folder):
    page_info = {}
    _pre_extract(page)
    screenshot_path = os.path.join(log_folder, 'screenshots', 'screenshot_pre.png')
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

    answer: list[str] = [x.message.content for x in response.choices]
    return answer


def execute_action(action, action_set, page, context, task_description, interactive_elements, log_folder):
    code, function_calls = action_set.to_python_code(action)
    for function_name, function_args in function_calls:
        extracted_number = parse_function_args(function_args)
        result = search_interactive_elements(interactive_elements, extracted_number)
        result['action'] = action
        result["url"] = page.url
        result['task_description'] = task_description
        logger.info(result)
        file_path = os.path.join(log_folder, 'flow', 'steps.json')
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


def capture_post_action_feedback(page, action, goal, log_folder):
    screenshot_path_post = os.path.join(log_folder, 'screenshots', 'screenshot_post.png')
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
                'title': element.get('title'),
                'ariaLabel': element.get('ariaLabel')
            }
    return {}  # Return empty dictionary if no matching element is found


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
