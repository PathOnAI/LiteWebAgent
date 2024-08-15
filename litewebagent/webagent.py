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
from litewebagent.observation.extract_elements import (extract_interactive_elements, highlight_elements)
#, extract_interactive_elements_more_info
from playwright.sync_api import sync_playwright
from openai import OpenAI
from dotenv import load_dotenv
from openai import OpenAI
# from litellm import completion
import os
import json
_ = load_dotenv()


openai_client = OpenAI()
import argparse
from litewebagent.action.highlevel import HighLevelActionSet
from litewebagent.playwright_manager import PlaywrightManager, get_browser, get_context, get_page, playwright_manager
from litewebagent.action.base import execute_python_code

from playwright.sync_api import sync_playwright
from urllib.parse import urlparse
import time
import inspect
from bs4 import BeautifulSoup
import logging
from litewebagent.agents.DemoAgent import DemoAgent
from litewebagent.agents.HighLevelPlanningAgent import HighLevelPlanningAgent
from litewebagent.agents.ContextAwarePlanningAgent import ContextAwarePlanningAgent

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
# "extract all product names of the website screenshot"

import base64


def parse_function_args(function_args):
    if not function_args or not isinstance(function_args, list):
        return None

    first_arg = function_args[0]

    # Check if the first argument is a string that represents a number
    if isinstance(first_arg, str) and first_arg.replace('.', '', 1).isdigit():
        return first_arg

    return None


def append_to_steps_json(result, file_path):
    # Convert the result to a JSON string
    json_line = json.dumps(result)

    # Append the JSON string as a new line in the file
    with open(file_path, 'a') as file:
        file.write(json_line + '\n')

    print(f"Appended result to {file_path}")

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def scan_page_extract_information(instruction):
    page = get_page()
    import time
    time.sleep(2)
    page.screenshot(path='./playground/gpt4v/screenshot.png', full_page=True)
    html_content = page.content()
    main_content = page.evaluate('''() => {
                    let main = document.querySelector('main');
                    if (!main) {
                        main = document.body;
                    }

                    const clone = main.cloneNode(true);

                    const unwantedTags = ['script', 'style', 'link', 'meta', 'noscript', 'iframe'];
                    unwantedTags.forEach(tag => {
                        clone.querySelectorAll(tag).forEach(el => el.remove());
                    });

                    clone.querySelectorAll('svg').forEach(svg => {
                        while (svg.firstChild) {
                            svg.removeChild(svg.firstChild);
                        }
                    });

                    // Remove data- attributes and limit classes to 3
                    clone.querySelectorAll('*').forEach(el => {
                        [...el.attributes].forEach(attr => {
                            if (attr.name.startsWith('data-')) {
                                el.removeAttribute(attr.name);
                            } else if (attr.name === 'class') {
                                let classes = attr.value.split(/\\s+/);
                                if (classes.length > 3) {
                                    el.className = classes.slice(0, 3).join(' ');
                                }
                            }
                        });
                    });

                    return clone.innerHTML;
                }''')
    with open('./playground/gpt4v/main_content.html', 'w') as f:
        f.write(main_content)

    import base64
    from mimetypes import guess_type

    def local_image_to_data_url(image_path):
        mime_type, _ = guess_type(image_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'

        with open(image_path, "rb") as image_file:
            base64_encoded_data = base64.b64encode(image_file.read()).decode('utf-8')

        return f"data:{mime_type};base64,{base64_encoded_data}"

    image_path = './playground/gpt4v/screenshot.png'
    image_data_url = local_image_to_data_url(image_path)

    with open('./playground/gpt4v/main_content.html', 'r') as file:
        html_content = file.read()

    import openai
    from dotenv import load_dotenv
    _ = load_dotenv()

    from openai import OpenAI
    # openai_client = OpenAI()

    # https://platform.openai.com/docs/guides/vision
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
                    # {"type": "text", "text": f"HTML content: {html_content}"}
                ]
            }
        ]
    )

    content = response.choices[0].message.content
    return f"Scanned the page content according to your instruction {instruction}. Here's the answer:\n\n{content}"


def take_action(goal, agent_type):
    try:
        # Setup
        context = get_context()
        page = get_page()
        action_set = HighLevelActionSet(
            subsets=agent_type,
            strict=False,
            multiaction=True,
            demo_mode="default"
        )

        # Extract page information
        # screenshot = extract_screenshot(page)
        time.sleep(3)
        _pre_extract(page)
        dom = extract_dom_snapshot(page)
        axtree = extract_merged_axtree(page)
        focused_element_bid = extract_focused_element_bid(page)
        extra_properties = extract_dom_extra_properties(dom)
        # Flatten DOM and accessibility tree
        # Import necessary utilities
        from browsergym.utils.obs import flatten_axtree_to_str, flatten_dom_to_str, prune_html
        dom_txt = flatten_dom_to_str(dom)
        axtree_txt = flatten_axtree_to_str(axtree)
        interactive_elements = extract_interactive_elements(page)
        highlight_elements(page, interactive_elements)
        screenshot_path_pre = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_pre.png')
        page.screenshot(path=screenshot_path_pre)
        _post_extract(page)
        url = page.url

        # Prepare messages for AI model
        system_msg = f"""
        # Instructions
        Review the current state of the page and all other information to find the best
        possible next action to accomplish your goal. Your answer will be interpreted
        and executed by a program, make sure to follow the formatting instructions.

        Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
        # Goal:
        {goal}"""

        prompt = f"""
        # Current Accessibility Tree:
        {axtree_txt}

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

        # Query OpenAI model
        base64_image = encode_image(screenshot_path_pre)
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

        action = response.choices[0].message.content

        # Execute the action
        try:
            code, function_calls = action_set.to_python_code(action)
            for function_name, function_args in function_calls:
                print(function_name, function_args)
                extracted_number = parse_function_args(function_args)

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

            result = search_interactive_elements(interactive_elements, extracted_number)
            print(result)
            result['action'] = action
            result["url"] = url
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
            page = get_page()
            screenshot_path_post = os.path.join(os.getcwd(), 'litewebagent', 'screenshots', 'screenshot_post.png')
            time.sleep(3)
            page.screenshot(path=screenshot_path_post)
            # _pre_extract(page)
            # dom = extract_dom_snapshot(page)
            # axtree = extract_merged_axtree(page)
            # axtree_txt = flatten_axtree_to_str(axtree)
            # focused_element_bid = extract_focused_element_bid(page)
            # extra_properties = extract_dom_extra_properties(dom)
            # _post_extract(page)
            base64_image = encode_image(screenshot_path_post)
            prompt = f"""
            After we take action {action}, a screenshot was captured.

            # Screenshot description:
            The image provided is a screenshot of the application state after the action was performed.


            # The original goal:
            {goal}

            Based on the screenshot and the updated Accessibility Tree, is the goal finished now? Provide an answer and explanation, referring to visual elements from the screenshot if relevant.
            """

            # Query OpenAI model
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

            feedback = response.choices[0].message.content

            return f"The action is: {action} - the result is: {feedback}"
        except Exception as e:
            last_action_error = f"{type(e).__name__}: {str(e)}"
            logger.error(f"Action execution failed: {last_action_error}")
            return f"{action} - Task failed with action error: {last_action_error}"

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"Task failed: {error_msg}")
        return f"Task failed: {error_msg}"


def upload_file(goal):
    response = take_action(goal, ["file"])
    return response
def navigation(goal):
    response = take_action(goal, ["bid", "nav"])
    return response



tools = [
    {
        "type": "function",
        "function": {
            "name": "navigation",
            "description": "Perform a web navigation task, including click, search ",
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
    },
    {
        "type": "function",
        "function": {
            "name": "upload_file",
            "description": "upload file.",
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
    },
]

client = OpenAI()
available_tools = {
    "navigation": navigation,
    "upload_file": upload_file,
    "scan_page_extract_information": scan_page_extract_information,
}

# set up web agent
# use web agent

def setup_web_agent(starting_url, goal, model_name="gpt-4o-mini", agent_type="DemoAgent"):
    messages = [
        {
            "role": "system",
            "content": """You are a web search agent designed to perform specific tasks on web pages as instructed by the user. Your primary objectives are:

    1. Execute ONLY the task explicitly provided by the user.
    2. Perform the task efficiently and accurately using the available functions.
    3. If there are errors, retry using a different approach within the scope of the given task.
    4. Once the current task is completed, stop and wait for further instructions.

    Critical guidelines:
    - Strictly limit your actions to the current task. Do not attempt additional tasks or next steps.
    - Use only the functions provided to you. Do not attempt to use functions or methods that are not explicitly available.
    - For navigation or interaction with page elements, always use the appropriate bid (browser element ID) when required by a function.
    - Do not try to navigate to external websites or use URLs directly.
    - If a task cannot be completed with the available functions, report the limitation rather than attempting unsupported actions.
    - After completing a task, report its completion and await new instructions. Do not suggest or initiate further actions.

    Remember: Your role is to execute the given task precisely as instructed, using only the provided functions and within the confines of the current web page. Do not exceed these boundaries under any circumstances."""
        }
    ]
    file_path = os.path.join('litewebagent', 'flow', 'steps.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    page = get_page()
    page.goto(starting_url)

    # Save starting_url as the first line in the file
    with open(file_path, 'w') as file:
        file.write(starting_url + '\n')

    # # Create an empty file
    # open(file_path, 'w').close()
    if agent_type == "DemoAgent":
        agent = DemoAgent(model_name=model_name, tools=tools, available_tools=available_tools, messages=messages, goal = goal)
    elif agent_type == "HighLevelPlanningAgent":
        agent = HighLevelPlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools, messages=messages, goal=goal)
    elif agent_type == "ContextAwarePlanningAgent":
        agent = ContextAwarePlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal)
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'DemoAgent' or 'HighLevelPlanningAgent'."
        logger.error(error_message)
        return {"error": error_message}
    return agent

    # response = agent.send_prompt(plan)
    # print("agent message list:\n")
    # print(agent.messages)
    # return response


# def use_web_agent(agent, plan):

def main(args):
    browser = get_browser()
    context = get_context()
    page = get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    # page.goto("https://www.amazon.com/s?k=dining+table&crid=1FQ2714L2KJLK&sprefix=dining+tabl%2Caps%2C235&ref=nb_sb_noss_2")
    # description = "Scan the whole page to extract product names"
    # response = use_web_agent(description, "gpt-4o-mini")
    # print(response)
    #page.goto("https://www.airbnb.com")
    starting_url = "https://www.airbnb.com"
    plan = "(1) enter the 'San Francisco' as destination, (2) and click search"
    goal = "set destination as San Francisco, then search the results"
    agent = setup_web_agent(starting_url, goal, model_name=args.model, agent_type=args.agent_type)
    response = agent.send_prompt(plan)
    print(response)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="DemoAgent",
                        choices=["DemoAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent"],
                        help="Type of agent to use (default: DemoAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--workflow_index', type=int, default=5,
                        help="Index of the workflow to use from the JSON file (default: 5)")
    args = parser.parse_args()
    main(args)