import sys
import os
import argparse
import logging
from dotenv import load_dotenv
from openai import OpenAI
from litewebagent.playwright_manager import get_browser, get_context, get_page, playwright_manager
from litewebagent.agents.DemoAgent import DemoAgent
from litewebagent.agents.HighLevelPlanningAgent import HighLevelPlanningAgent
from litewebagent.agents.ContextAwarePlanningAgent import ContextAwarePlanningAgent
from litewebagent.functions.functions import navigation, upload_file, scan_page_extract_information, take_action, select_option

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ = load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
openai_client = OpenAI()

# Define the default features
DEFAULT_FEATURES = ['screenshot', 'dom', 'axtree', 'focused_element', 'extra_properties', 'interactive_elements']


def create_function_wrapper(func, features):
    def wrapper(task_description):
        return func(task_description, features)

    return wrapper


tools = [
    {
        "type": "function",
        "function": {
            "name": "navigation",
            "description": "Perform a web navigation task, including click, search ",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_description": {
                        "type": "string",
                        "description": "The description of the web navigation task"
                    },
                },
                "required": [
                    "task_description",
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
                    "task_description": {
                        "type": "string",
                        "description": "The description of the web navigation task"
                    },
                },
                "required": [
                    "task_description",
                ]
            }
        }
    },
    {
            "type": "function",
            "function": {
                "name": "select_option",
                "description": "Select an option from a dropdown or list.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "task_description": {
                            "type": "string",
                            "description": "The description of the option selection task"
                        }
                    },
                    "required": [
                        "task_description"
                    ]
                }
            }
        }
]


def setup_web_agent(starting_url, goal, model_name="gpt-4o-mini", agent_type="DemoAgent", features=['axtree']):
    if features is None:
        features = DEFAULT_FEATURES

    available_tools = {
        "navigation": create_function_wrapper(navigation, features),
        "upload_file": create_function_wrapper(upload_file, features),
        "select_option": create_function_wrapper(select_option, features),
        # "scan_page_extract_information": scan_page_extract_information,
    }

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
    # Maximize the window on macOS
    page.set_viewport_size({"width": 1440, "height": 900})

    with open(file_path, 'w') as file:
        file.write(goal + '\n')
        file.write(starting_url + '\n')

    if agent_type == "DemoAgent":
        agent = DemoAgent(model_name=model_name, tools=tools, available_tools=available_tools, messages=messages,
                          goal=goal)
    elif agent_type == "HighLevelPlanningAgent":
        agent = HighLevelPlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal)
    elif agent_type == "ContextAwarePlanningAgent":
        agent = ContextAwarePlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                          messages=messages, goal=goal)
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'DemoAgent', 'HighLevelPlanningAgent', or 'ContextAwarePlanningAgent'."
        logger.error(error_message)
        return {"error": error_message}
    return agent


def main(args):
    browser = get_browser()
    context = get_context()
    page = get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    starting_url = "https://www.airbnb.com"
    plan = "(1) enter the 'San Francisco' as destination, (2) and click search"
    goal = "set destination as San Francisco, then search the results"

    # Use the features from command-line arguments
    features = args.features.split(',') if args.features else None

    agent = setup_web_agent(starting_url, goal, model_name=args.model, agent_type=args.agent_type, features=features)
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
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: None, which uses all features)")
    args = parser.parse_args()
    main(args)