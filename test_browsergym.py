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
_ = load_dotenv()


from litewebagent.playwright_manager import get_page
from action.highlevel import HighLevelActionSet
action_set = HighLevelActionSet(
        #subsets=["chat", "bid"],  # define a subset of the action space
        subsets = ["chat", "infeas", "bid", "coord", "nav", "tab"],
        # subsets=["chat", "bid", "coord"] # allow the agent to also use x,y coordinates
        strict=False,  # less strict on the parsing of the actions
        multiaction=True,  # enable to agent to take multiple actions at once
        demo_mode="default",  # add visual effects
    )

from openai import OpenAI

openai_client = OpenAI()



page = get_page()
print(page)
page.goto("https://www.google.com")
print(page)

def take_action(page, goal):
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
        model= "gpt-4o-mini",
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
        execute_python_code(
                        code,
                        page,
                        send_message_to_user=None,
                        report_infeasible_instructions=None,
                    )
    except Exception as e:
        last_action_error = f"{type(e).__name__}: {e}"
        print(last_action_error)


goal = "search dining table"
take_action(page, goal)
goal = "search dining table"
take_action(page, goal)
goal = "search dining table"
take_action(page, goal)
