import sys
import os
import logging
from dotenv import load_dotenv
from openai import OpenAI
from ..agents.FunctionCallingAgents.FunctionCallingAgent import FunctionCallingAgent
from ..agents.FunctionCallingAgents.HighLevelPlanningAgent import HighLevelPlanningAgent
from ..agents.FunctionCallingAgents.ContextAwarePlanningAgent import ContextAwarePlanningAgent
from ..webagent_utils_async.utils.utils import setup_logger
from ..webagent_utils_async.utils.playwright_manager import setup_playwright
from ..webagent_utils_async.tools.registry import ToolRegistry

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_ = load_dotenv()

logger = logging.getLogger(__name__)
openai_client = OpenAI()

# Define the default features
DEFAULT_FEATURES = ['screenshot', 'dom', 'axtree', 'focused_element', 'extra_properties', 'interactive_elements']


def create_function_wrapper(func, features, branching_factor, playwright_manager, log_folder, elements_filter):
    def wrapper(task_description):
        return func(task_description, features, branching_factor, playwright_manager, log_folder, elements_filter)

    return wrapper


async def setup_function_calling_web_agent(starting_url, goal, playwright_manager, model_name="gpt-4o-mini", agent_type="DemoAgent",
                                     features=['axtree'], tool_names = ["navigation", "select_option", "upload_file", "webscraping"],
                                     branching_factor=None, log_folder="log", elements_filter=None):
    logger = setup_logger()

    if features is None:
        features = DEFAULT_FEATURES

    tool_registry = ToolRegistry()
    available_tools = {}
    tools = []
    for tool_name in tool_names:
        available_tools[tool_name] = create_function_wrapper(tool_registry.get_tool(tool_name).func, features,
                                                             branching_factor, playwright_manager, log_folder, elements_filter=elements_filter)
        tools.append(tool_registry.get_tool_description(tool_name))

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
    - If a task cannot be completed with the available functions, report the limitation rather than attempting unsupported actions.
    - After completing a task, report its completion and await new instructions. Do not suggest or initiate further actions.

    Remember: Your role is to execute the given task precisely as instructed, using only the provided functions and within the confines of the current web page. Do not exceed these boundaries under any circumstances."""
        }
    ]
    # file_path = os.path.join(log_folder, 'flow', 'steps.json')
    # os.makedirs(os.path.dirname(file_path), exist_ok=True)

    page = await playwright_manager.get_page()
    if starting_url!=None:
        await page.goto(starting_url)

    # Maximize the window on macOS
    # page.set_viewport_size({"width": 1440, "height": 900})


    if agent_type == "FunctionCallingAgent":
        agent = FunctionCallingAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                     messages=messages,
                                     goal=goal, playwright_manager=playwright_manager, log_folder=log_folder)
    elif agent_type == "HighLevelPlanningAgent":
        agent = HighLevelPlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                       messages=messages, goal=goal, playwright_manager=playwright_manager,
                                       log_folder=log_folder)
    elif agent_type == "ContextAwarePlanningAgent":
        agent = ContextAwarePlanningAgent(model_name=model_name, tools=tools, available_tools=available_tools,
                                          messages=messages, goal=goal, playwright_manager=playwright_manager,
                                          log_folder=log_folder)
    else:
        error_message = f"Unsupported agent type: {agent_type}. Please use 'FunctionCallingAgent', 'HighLevelPlanningAgent', 'ContextAwarePlanningAgent', 'PromptAgent' or 'PromptSearchAgent' ."
        logger.error(error_message)
        return {"error": error_message}
    return agent