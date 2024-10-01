import os
from litewebagent.browser_env.extract_elements import remove_highlights
from litewebagent.action.base import execute_python_code
import ast
import pyparsing as pp
from litewebagent.browser_env.extract_elements import flatten_interactive_elements_to_str
from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str

from litewebagent.utils.utils import parse_function_args, append_to_steps_json, search_interactive_elements
import logging

logger = logging.getLogger(__name__)


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
