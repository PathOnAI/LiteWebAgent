import sys
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from litewebagent.agents.FunctionCallingAgents.FunctionCallingAgent import FunctionCallingAgent
from litewebagent.agents.FunctionCallingAgents.HighLevelPlanningAgent import HighLevelPlanningAgent
from litewebagent.agents.FunctionCallingAgents.ContextAwarePlanningAgent import ContextAwarePlanningAgent
from litewebagent.agents.SearchAgents.PromptSearchAgent import PromptSearchAgent
from litewebagent.agents.PromptAgents.PromptAgent import PromptAgent
from litewebagent.utils.fc_functions import navigation, upload_file, select_option

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ = load_dotenv()

logger = logging.getLogger(__name__)
openai_client = OpenAI()

# Define the default features
DEFAULT_FEATURES = ['screenshot', 'dom', 'axtree', 'focused_element', 'extra_properties', 'interactive_elements']


def create_function_wrapper(func, features, branching_factor, playwright_manager, log_folder):
    def wrapper(task_description):
        return func(task_description, features, branching_factor, playwright_manager, log_folder)

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


def setup_web_agent(starting_url, goal, model_name="gpt-4o-mini", agent_type="DemoAgent", features=['axtree'], branching_factor = None, playwright_manager = None, log_folder="log"):
    if features is None:
        features = DEFAULT_FEATURES


    available_tools = {
        "navigation": create_function_wrapper(navigation, features, branching_factor, playwright_manager, log_folder),
        "upload_file": create_function_wrapper(upload_file, features, branching_factor, playwright_manager, log_folder),
        "select_option": create_function_wrapper(select_option, features, branching_factor, playwright_manager, log_folder),
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
    file_path = os.path.join(log_folder, 'flow', 'steps.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    page = playwright_manager.get_page()
    page.goto(starting_url)
    # Maximize the window on macOS
    page.set_viewport_size({"width": 1440, "height": 900})

    with open(file_path, 'w') as file:
        file.write(goal + '\n')
        file.write(starting_url + '\n')

    if agent_type == "FunctionCallingAgent":
        agent = FunctionCallingAgent(model_name=model_name, tools=tools, available_tools=available_tools, messages=messages,
                          goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    elif agent_type == "PromptAgent":
        agent = PromptAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    elif agent_type == "HighLevelPlanningAgent":
        agent = HighLevelPlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    elif agent_type == "ContextAwarePlanningAgent":
        agent = ContextAwarePlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                          messages=messages, goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'FunctionCallingAgent', 'HighLevelPlanningAgent', 'ContextAwarePlanningAgent', 'PromptAgent' or 'PromptSearchAgent' ."
        logger.error(error_message)
        return {"error": error_message}
    return agent


def setup_search_agent(starting_url, goal, model_name="gpt-4o-mini", agent_type="PromptSearchAgent", features=['axtree'], branching_factor = None, playwright_manager = None, log_folder="log"):
    if features is None:
        features = DEFAULT_FEATURES


    available_tools = {
        "navigation": create_function_wrapper(navigation, features, branching_factor, playwright_manager, log_folder),
        "upload_file": create_function_wrapper(upload_file, features, branching_factor, playwright_manager, log_folder),
        "select_option": create_function_wrapper(select_option, features, branching_factor, playwright_manager, log_folder),
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
    file_path = os.path.join(log_folder, 'flow', 'steps.json')
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    page = playwright_manager.get_page()
    page.goto(starting_url)
    # Maximize the window on macOS
    page.set_viewport_size({"width": 1440, "height": 900})

    with open(file_path, 'w') as file:
        file.write(goal + '\n')
        file.write(starting_url + '\n')

    if agent_type == "PromptSearchAgent":
        agent = PromptSearchAgent(starting_url=starting_url, model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'FunctionCallingAgent', 'HighLevelPlanningAgent', 'ContextAwarePlanningAgent', 'PromptAgent' or 'PromptSearchAgent' ."
        logger.error(error_message)
        return {"error": error_message}
    return agent