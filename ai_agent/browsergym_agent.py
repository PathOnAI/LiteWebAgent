import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from observation.constants import TEXT_MAX_LENGTH, BROWSERGYM_ID_ATTRIBUTE, EXTRACT_OBS_MAX_TRIES
from observation.observation import (
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
from utils import *
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
from litellm import completion

openai_client = OpenAI()
from playwright_manager import get_browser, get_context, get_page
from action.highlevel import HighLevelActionSet
browser = get_browser()
context = get_context()
page = get_page()
page.goto("https://www.google.com")


def take_action(goal):
    context = get_context()
    page = get_page()
    subsets = ["chat"]
    agent_type = ["bid", "nav"]
    subsets.extend(agent_type)
    action_set = HighLevelActionSet(
        subsets=subsets,
        strict=False,  # less strict on the parsing of the actions
        multiaction=True,  # enable to agent to take multiple actions at once
        demo_mode="default",  # add visual effects
    )
    _pre_extract(page)
    dom = extract_dom_snapshot(page)
    axtree = extract_merged_axtree(page)
    focused_element_bid = extract_focused_element_bid(page)
    extra_properties = extract_dom_extra_properties(dom)
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
    response = completion(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user", "content": prompt},
        ],
    )
    action = response.choices[0].message.content
    # print(action)
    code = action_set.to_python_code(action)
    # print(code)
    from action.base import execute_python_code
    try:
        # write_to_file("script.py", code)
        execute_python_code(
            code,
            page,
            context,
            send_message_to_user=None,
            report_infeasible_instructions=None,
        )
        return action + "task succeeded"

    except Exception as e:
        last_action_error = f"{type(e).__name__}: {str(e)}"
        print(last_action_error)
        return action + "task failed with action" + last_action_error



from dotenv import load_dotenv
from openai import OpenAI
import os
_ = load_dotenv()

tools = [
    {
        "type": "function",
        "function": {
            "name": "take_action",
            "description": "Perform a web navigation task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The description of the web navigation task"
                    },
                },
                "required": [
                    "goal",
                ]
            }
        }
    }
]

client = OpenAI()
available_tools = {
    "take_action": take_action,
}

def use_browsergym_agent(description):
    messages = [Message(role="system",
                        content="You are a smart web search agent to perform search and click task for customers")]
    send_prompt(client, messages, description, tools, available_tools)
    return messages[-1].content


def main():
    try:
        # Example usage of the search and redirect agent
        tasks = ["(1) search dining table, (2) click google search, (3) go to amazon.com, (4) search dining table, (5) click search"]
        for description in tasks:
            response = use_browsergym_agent(description)
            print("Search and Redirect Agent Response:")
            print(response)
    finally:
        # Make sure to close the Playwright instance when done
        from playwright_manager import close_playwright
        close_playwright()

if __name__ == "__main__":
    main()