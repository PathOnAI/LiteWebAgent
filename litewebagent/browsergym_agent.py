import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from litewebagent.observation.constants import TEXT_MAX_LENGTH, BROWSERGYM_ID_ATTRIBUTE, EXTRACT_OBS_MAX_TRIES
from litewebagent.observation.observation import (
    _pre_extract,
    _post_extract,
    extract_screenshot,
    extract_dom_snapshot,
    extract_dom_extra_properties,
    extract_merged_axtree,
    extract_focused_element_bid,
    MarkingError,
)

from dotenv import load_dotenv
import playwright
_ = load_dotenv()
import time
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)



from openai import OpenAI

openai_client = OpenAI()
from playwright_manager import get_browser, get_context, get_page
from action.highlevel import HighLevelActionSet
browser = get_browser()
context = get_context()
page = get_page()
page.goto("https://www.google.com")

def write_to_file(file_path: str, text: str, encoding: str = "utf-8") -> str:
    try:
        directory = os.path.dirname(file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(file_path, "w", encoding=encoding) as f:
            f.write(text)
        return "File written successfully."
    except Exception as error:
        return f"Error: {error}"


def take_action(context, page, goal, agent_type):
    from playwright_manager import get_page
    from action.highlevel import HighLevelActionSet
    subsets = ["chat"]
    subsets.extend(agent_type)
    action_set = HighLevelActionSet(
        subsets=subsets,
        strict=False,  # less strict on the parsing of the actions
        multiaction=True,  # enable to agent to take multiple actions at once
        demo_mode="default",  # add visual effects
    )
    _pre_extract(page)
    dom = extract_dom_snapshot(page)
    # print(dom)
    axtree = extract_merged_axtree(page)
    focused_element_bid = extract_focused_element_bid(page)
    extra_properties = extract_dom_extra_properties(dom)
    # print(axtree)
    # print(focused_element_bid)
    # print(extra_properties)
    # post-extraction cleanup of temporary info in dom
    _post_extract(page)
    from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
    dom_txt = flatten_dom_to_str(dom),
    axtree_txt = flatten_axtree_to_str(axtree)

    system_msg = f"""\
    # Instructions
    Review the current state of the page and all other information to find the best
    possible next action to accomplish your goal. Your answer will be interpreted
    and executed by a program, make sure to follow the formatting instructions.

    Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
    # Goal:
    {goal}"""

    prompt = f"""\

    # Current Accessibility Tree:
    {axtree_txt}


    # Action Space
    {action_set.describe(with_long_description=False, with_examples=True)}

    Here is an example with chain of thought of a valid action when clicking on a button:
    "
    In order to accomplish my goal I need to click on the button with bid 12
    ```click("12")```
    "
    """

    # query OpenAI model
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
    )
    action = response.choices[0].message.content
    print(action)
    code = action_set.to_python_code(action)
    # print(code)
    from action.base import execute_python_code
    try:
        write_to_file("script.py", code)
        execute_python_code(
            code,
            page,
            context,
            send_message_to_user=None,
            report_infeasible_instructions=None,
        )

    except Exception as e:
        last_action_error = f"{type(e).__name__}: {str(e)}"
        print(last_action_error)


goal = "search dining table"
take_action(context, page, goal, ["bid"])
goal = "click google search"
take_action(context, page, goal, ["bid"])
