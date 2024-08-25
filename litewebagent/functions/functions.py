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
from litewebagent.functions.utils import *

logger = logging.getLogger(__name__)
openai_client = OpenAI()


import ast
import pyparsing as pp
from typing import Any
from collections import defaultdict

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
