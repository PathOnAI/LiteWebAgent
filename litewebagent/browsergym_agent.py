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


def send_completion_request(messages, agent_type, depth: int = 0):
    if depth >= 8:
        return "retry upper bound, task failed"
    # print(messages)
    # import pdb; pdb.set_trace()
    context = get_context()
    page = get_page()
    subsets=["chat"]
    subsets.extend(agent_type)
    action_set = HighLevelActionSet(
        subsets= subsets,
        strict=False,  # less strict on the parsing of the actions
        multiaction=True,  # enable to agent to take multiple actions at once
        demo_mode="default",  # add visual effects
    )
    for retries_left in reversed(range(EXTRACT_OBS_MAX_TRIES)):
        try:
            # pre-extraction, mark dom elements (set bid, set dynamic attributes like value and checked)
            _pre_extract(page)

            dom = extract_dom_snapshot(page)
            axtree = extract_merged_axtree(page)
            focused_element_bid = extract_focused_element_bid(page)
            extra_properties = extract_dom_extra_properties(dom)
        except (playwright.sync_api.Error, MarkingError) as e:
            err_msg = str(e)
            # try to add robustness to async events (detached / deleted frames)
            if retries_left > 0 and (
                    "Frame was detached" in err_msg
                    or "Frame with the given frameId is not found" in err_msg
                    or "Execution context was destroyed" in err_msg
                    or "Frame has been detached" in err_msg
                    or "Cannot mark a child frame without a bid" in err_msg
            ):
                logger.warning(
                    f"An error occured while extracting the dom and axtree. Retrying ({retries_left}/{EXTRACT_OBS_MAX_TRIES} tries left).\n{repr(e)}"
                )
                # post-extract cleanup (aria-roledescription attribute)
                _post_extract(page)
                time.sleep(0.5)
                continue
            else:
                raise e
        break



    # _pre_extract(page)
    # dom = extract_dom_snapshot(page)
    # axtree = extract_merged_axtree(page)
    # focused_element_bid = extract_focused_element_bid(page)
    # extra_properties = extract_dom_extra_properties(dom)
    _post_extract(page)
    from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
    dom_txt = flatten_dom_to_str(dom),
    axtree_txt = flatten_axtree_to_str(axtree)


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
    temp_messages = messages.copy()
    temp_messages.append({"role": "user", "content": prompt})
    # print(temp_messages)
    response = openai_client.chat.completions.create(
        model= "gpt-4o-mini",
        messages=temp_messages
    )
    action = response.choices[0].message.content
    print(action)
    if 'send_msg_to_user' in action:
        return action
    if 'noop' in action:
        return "task finished"
    code = action_set.to_python_code(action)
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
        messages.append({"role": "assistant", "content": action+"succeeded"})
    except Exception as e:
        last_action_error = f"{type(e).__name__}: {str(e)}"
        print("error is:\n")
        print(last_action_error)
        messages.append({"role": "assistant", "content": action + last_action_error})
    return send_completion_request(messages, agent_type, depth+1)








# goal = "open a new tab, go to amazon"
# take_action(goal, ["tab", "nav"])
# ## TODO: now we have a new page? extract the page?
#


# ## the agent is still working on the original page
# goal = "just go to amazon"
# system_msg = f"""\
#     # Instructions
#     Review the current state of the page and all other information to find the best
#     possible next action to accomplish your goal. Your answer will be interpreted
#     and executed by a program, make sure to follow the formatting instructions.
#
#     # Goal:
#     {goal}"""
# messages = [{"role": "system", "content": system_msg}]
# response = send_completion_request(messages, ["bid", "nav", "coord"], 0)
# print("XXXXXXXXXXXXXXXX the response is XXXXXXXXXXXXXXXX:\n")
# print(response)


# goal = "hello!"
# system_msg = f"""\
#     # Instructions
#     Review the current state of the page and all other information to find the best
#     possible next action to accomplish your goal. Your answer will be interpreted
#     and executed by a program, make sure to follow the formatting instructions.
#
#     # Goal:
#     {goal}"""
# messages = [{"role": "system", "content": system_msg}]
# response = send_completion_request(messages, ["bid", "nav", "coord"], 0)
# print("XXXXXXXXXXXXXXXX the response is XXXXXXXXXXXXXXXX:\n")
# print(response)


def use_browsergym_agent(description):
    # goal = "just go to amazon"
    system_msg = f"""\
        # Instructions
        Review the current state of the page and all other information to find the best
        possible next action to accomplish your goal. Your answer will be interpreted
        and executed by a program, make sure to follow the formatting instructions.

        # Goal:
        {description}"""
    messages = [{"role": "system", "content": system_msg}]
    response = send_completion_request(messages, ["bid", "nav", "coord"], 0)
    print("XXXXXXXXXXXXXXXX the response is XXXXXXXXXXXXXXXX:\n")
    print(response)
    return response

def main():
    use_browsergym_agent("just go to amazon")
    # try:
    #     # Example usage of the navigation control agent
    #     description = "Go to url: https://huggingface.co/docs/peft/index, scroll down and Scan the whole page"
    #     response = use_navigation_control_agent(description)
    #     print("Navigation Control Agent Response:")
    #     print(response)
    # finally:
    #     # Make sure to close the Playwright instance when done
    #     from playwright_manager import close_playwright
    #     close_playwright()

if __name__ == "__main__":
    main()




