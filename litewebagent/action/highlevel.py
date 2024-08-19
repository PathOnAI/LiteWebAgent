# copied and modified from https://github.com/ServiceNow/BrowserGym
import inspect
import random

from dataclasses import dataclass
from typing import Literal, Optional

from . import utils
from .base import AbstractActionSet
from .playwright_functions import (
    noop,
    send_msg_to_user,
    report_infeasible,
    fill,
    # check,
    # uncheck,
    select_option,
    click,
    dblclick,
    hover,
    press,
    focus,
    clear,
    drag_and_drop,
    upload_file,
    scroll,
    mouse_move,
    mouse_up,
    mouse_down,
    mouse_click,
    mouse_dblclick,
    mouse_drag_and_drop,
    mouse_upload_file,
    keyboard_down,
    keyboard_up,
    keyboard_press,
    keyboard_type,
    keyboard_insert_text,
    # keyboard_insert_text_then_enter,
    tab_close,
    tab_focus,
    new_tab,
    go_back,
    go_forward,
    goto,
)
from .parsers import highlevel_action_parser, action_docstring_parser


CHAT_ACTIONS = [send_msg_to_user]

INFEAS_ACTIONS = [report_infeasible]

BID_ACTIONS = [
    scroll,
    fill,
    # These are not really needed and might pollute the action space, doing more harm than good
    # check,
    # uncheck,
    # select_option,
    click,
    dblclick,
    hover,
    press,
    focus,
    clear,
    drag_and_drop,
    upload_file,
]

FILE_ACTIONS = [
    upload_file,
]

SELECT_OPTION_ACTIONS = [
    select_option,
]

COORD_ACTIONS = [
    scroll,
    mouse_move,
    mouse_up,
    mouse_down,
    mouse_click,
    mouse_dblclick,
    mouse_drag_and_drop,
    mouse_upload_file,
    keyboard_down,
    keyboard_up,
    keyboard_press,
    keyboard_type,
    keyboard_insert_text,
    # keyboard_insert_text_then_enter,
]

NAV_ACTIONS = [go_back, go_forward, goto]

TAB_ACTIONS = [
    tab_close,
    tab_focus,
    new_tab,
]


@dataclass
class HighLevelAction:
    # entrypoint: callable
    signature: str
    description: str
    examples: list[str]


class HighLevelActionSet(AbstractActionSet):

    ActionSubset = Literal["chat", "infeas", "bid", "coord", "nav", "tab", "custom"]

    def __init__(
        self,
        subsets: Optional[ActionSubset | list[ActionSubset]] = [
            "chat",
            "infeas",
            "bid",
            "nav",
            "tab",
        ],
        custom_actions: Optional[list[callable]] = None,
        multiaction: bool = True,
        demo_mode: Literal["off", "default", "all_blue", "only_visible_elements"] = "off",
        strict: bool = False,
    ):
        super().__init__(strict)
        self.multiaction = multiaction
        self.demo_mode = demo_mode

        if not subsets:
            raise ValueError(f"'action_subsets' is empty.")

        if isinstance(subsets, str):
            subsets = [subsets]

        allowed_actions = [noop]  # the noop action is always allowed

        # add actions from specified action sets
        if subsets:
            for subset in subsets:
                match subset:
                    case "chat":
                        allowed_actions.extend(CHAT_ACTIONS)
                    case "infeas":
                        allowed_actions.extend(INFEAS_ACTIONS)
                    case "select_option":
                        allowed_actions.extend(SELECT_OPTION_ACTIONS)
                    case "file":
                        allowed_actions.extend(FILE_ACTIONS)
                    case "bid":
                        allowed_actions.extend(BID_ACTIONS)
                    case "coord":
                        allowed_actions.extend(COORD_ACTIONS)
                    case "nav":
                        allowed_actions.extend(NAV_ACTIONS)
                    case "tab":
                        allowed_actions.extend(TAB_ACTIONS)
                    case "custom":
                        if not custom_actions:
                            raise ValueError(
                                "'custom' is in 'action_subsets' but 'custom_actions' is empty."
                            )
                        allowed_actions.extend(custom_actions)
                    case _:
                        raise ValueError(f"Unknown high-level action subspace: {subset}")

        # like set() but preserves order
        # https://stackoverflow.com/questions/1653970/does-python-have-an-ordered-set
        allowed_actions = list(dict.fromkeys(allowed_actions).keys())

        # parse the actions and build the action space
        self.action_set: dict[str, HighLevelAction] = {}
        self.python_includes = ""

        # include playwright imports
        self.python_includes += f"""\
import playwright.sync_api
from typing import Literal


"""
        # include demo_mode flag
        self.python_includes += f"""\
demo_mode={repr(demo_mode)}


"""

        # include utility functions
        for _, func in inspect.getmembers(utils, inspect.isfunction):
            self.python_includes += f"""\
{inspect.getsource(func)}


"""

        # parse and include action functions
        for func in allowed_actions:

            # include action function definition in the code
            self.python_includes += f"""\
{inspect.getsource(func)}


"""

            # extract action signature
            signature = f"{func.__name__}{inspect.signature(func)}"

            # parse docstring
            description, examples = action_docstring_parser.parse_string(func.__doc__)

            # reconstruct action description
            description = " ".join(description)

            # reconstruct action examples
            examples = [
                function_name + "(" + ", ".join([repr(arg) for arg in function_args]) + ")"
                for function_name, function_args in examples
            ]

            if func.__name__ in self.action_set:
                raise ValueError(f"Duplicated action '{func.__name__}'")

            self.action_set[func.__name__] = HighLevelAction(
                # entrypoint=func,
                signature=signature,
                description=description,
                examples=examples,
            )

    def example_action(self, abstract: bool, max_examples: int = 3) -> str:
        """
        Returns an example action as a string.
        """
        if abstract:
            if self.multiaction:
                return """\
One or several actions, separated by new lines."""
            else:
                return """\
One single action to be executed. You can only use one action at a time."""
        else:
            picked_examples = []

            # use fill and click examples if action is present
            for action_name in ["fill", "click", "mouse_click", "keyboard_type"]:
                if action_name in self.action_set:
                    picked_examples.extend(self.action_set[action_name].examples)

            # last resort, use all action examples
            if not picked_examples:
                for _, action in self.action_set.items():
                    picked_examples += action.examples

            # shuffle examples
            rng = random.Random(1)
            rng.shuffle(picked_examples)

            if self.multiaction:
                return "\n".join(picked_examples[:max_examples])
            else:
                return picked_examples[0]

    def describe(self, with_long_description: bool = True, with_examples: bool = True):
        """
        Returns a textual description of this action space.
        """
        description = f"""
{len(self.action_set)} different types of actions are available.

"""
        for _, action in self.action_set.items():
            description += f"""\
{action.signature}
"""

            if with_long_description:
                description += f"""\
    Description: {action.description}
"""
            if with_examples and action.examples:
                description += f"""\
    Examples:
"""
                for example in action.examples:
                    description += f"""\
        {example}

"""

        if self.multiaction:
            description += f"""\
Multiple actions can be provided at once, but will be executed sequentially without any feedback from the page.
More than 2-3 actions usually leads to failure or unexpected behavior."""
        else:
            description += f"""\
Only a single action can be provided at once."""

        example_action = self.example_action(abstract=False)
        if example_action:
            description += f""" Example:
{example_action}
"""
        else:
            description += f"""\

"""

        return description

    def to_python_code(self, action):
        """
        Converts the given high-level action string to browsergym-compatible python code.

        Args:
            action: the high-level action to parse.

        Returns:
            Executable python code that performs the action in a browsergym environment.
        """
        highlevel_code = action

        # do the actual parsing and convert each high-level action to
        # the corresponding python function call
        if self.strict:
            function_calls = highlevel_action_parser.parse_string(highlevel_code, parse_all=True)
        else:
            function_calls = highlevel_action_parser.search_string(
                highlevel_code
            )  # allow for multiple matches, skip anything in-between
            function_calls = sum(function_calls)  # unpack multiple matches

        if not function_calls:
            raise ValueError("Received an empty action.")
        elif len(function_calls) > 1 and not self.multiaction:
            raise ValueError("Received a multi-action, only single-actions are allowed.")

        python_code = ""

        # function definitions
        python_code += self.python_includes

        # # Add new functions
        python_code += """
def extract_code(text):
    # Split the text by triple backticks
    parts = text.split('```')

    # Check if we have at least one pair of triple backticks
    if len(parts) >= 3:
        # Return the content between the first pair of triple backticks
        return parts[1].strip()
    else:
        return "No code found between triple backticks"


def highlight_element_by_bid(page: playwright.sync_api.Page, bid: str, text: str):
    \"\"\"
    Highlights an element on the page by drawing a large bounding box around it
    and displaying custom text.

    Args:
        page: The Playwright page object.
        bid: The browser ID of the element to highlight.
        text: The custom text to display above the highlighted element.
    \"\"\"
    # Get the element using the bid
    elem = get_elem_by_bid(page, bid)

    # Get the bounding box of the element
    box = elem.bounding_box()

    if box:
        # Calculate enlarged box dimensions (50% larger)
        padding = min(box['width'], box['height']) * 0.25  # 25% padding
        enlarged_box = {
            'x': box['x'] - padding,
            'y': box['y'] - padding,
            'width': box['width'] + padding * 2,
            'height': box['height'] + padding * 2
        }

         # Load custom fonts from Google Fonts
        page.evaluate(\"\"\"
            (() => {
                const link = document.createElement('link');
                link.href = 'https://fonts.googleapis.com/css2?family=Raleway:wght@400;700&family=Roboto:wght@400;700&family=Hind+Siliguri:wght@400;700&display=swap';
                link.rel = 'stylesheet';
                document.head.appendChild(link);
            })()
        \"\"\")

        # Create a larger highlight with custom text
        page.evaluate(
            \"\"\"
            ([box, text]) => {
                const overlay = document.createElement('div');
                document.body.appendChild(overlay);
                overlay.setAttribute('style', `
                    all: initial;
                    position: fixed;
                    border: 2px solid #79bd9a;
                    borderRadius: 10px;
                    boxShadow: 0 0 0 4000px rgba(0, 0, 0, 0.1);
                    left: ${box.x}px;
                    top: ${box.y}px;
                    width: ${box.width}px;
                    height: ${box.height}px;
                    z-index: 2147483646;
                    pointerEvents: none;
                `);

                const textElement = document.createElement('div');
                textElement.textContent = text;
                textElement.setAttribute('style', `
                    position: absolute;
                    top: -40px;
                    left: 50%;
                    transform: translateX(-50%);
                    background-color: #79bd9a;
                    color: white;
                    padding: 8px 10px;
                    border-radius: 10px;
                    fontFamily: Roboto, Raleway, Hind Siliguri;
                    fontSize: 16px;
                    fontWeight: bold;
                `);
                overlay.appendChild(textElement);

                setTimeout(() => {
                    document.body.removeChild(overlay);
                }, 5000);  // Remove after 5 seconds
            }
            \"\"\",
            [enlarged_box, text]
        )

        # Wait for the highlight to be visible
        page.wait_for_timeout(5000)  # Wait for 5 seconds

def extract_bid_from_action(action: str) -> str:
    \"\"\"
    Extracts the bid from the action string.

    Args:
        action: The action string containing the bid.

    Returns:
        The extracted bid as a string.
    \"\"\"
    import re

    # Use regex to find the bid within the single quotes
    print(action)
    match = re.search(r"'(\\w+)'", action)
    if match:
        return match.group(1)
    else:
        raise ValueError("No bid found in the action string")

# Modified execute_action function
def execute_action(action: str):
    # Extract the bid from the action
    extracted_code = extract_code(action)
    bid = extract_bid_from_action(extracted_code)

    # Highlight the element
    highlight_element_by_bid(page, bid, action)
        """
        python_code += """\n"""
        python_code += f'action="""{highlevel_code}"""\n'
        python_code += """execute_action(action)\n"""
        # function calls
        for function_name, function_args in function_calls:
            if function_name not in self.action_set:
                raise NameError(f"Invalid action type '{function_name}'.")
            python_code += (
                function_name + "(" + ", ".join([repr(arg) for arg in function_args]) + ")\n"
            )
        # return the constructed python code
        return python_code, function_calls
