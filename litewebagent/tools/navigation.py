from litewebagent.tools.shared_utils import take_action
from litewebagent.tools.registry import ToolRegistry, Tool


def navigation(task_description, features=None, branching_factor=None, playwright_manager=None, log_folder='log'):
    response = take_action(task_description, ["bid", "nav"], features, branching_factor, playwright_manager, log_folder)
    return response


def register_navigation_tool():
    ToolRegistry.register(Tool(
        name="navigation",
        func=navigation,
        description="Perform a web navigation task, including fill text, click, search, go to new page",
        parameters={
            "task_description": {
                "type": "string",
                "description": "The description of the web navigation task, including fill text, click, search, go to new page"
            }
        }
    ))
