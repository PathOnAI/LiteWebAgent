# copied and modified from https://github.com/ServiceNow/BrowserGym
import playwright.async_api
from abc import ABC, abstractmethod


class AbstractActionSet(ABC):
    def __init__(self, strict: bool = False):
        self.strict = strict

    @abstractmethod
    def describe(self, with_long_description: bool = True, with_examples: bool = True) -> str:
        """
        Returns a textual description of this action space.
        """

    @abstractmethod
    def example_action(self, abstract: bool) -> str:
        """
        Returns an example action as a string.
        """

    @abstractmethod
    def to_python_code(self, action) -> str:
        """
        Converts the given action to browsergym-compatible python code.

        Args:
            action: the action to convert.

        Returns:
            Executable python code that performs the action in a browsergym environment.
        """


async def execute_python_code(
        code: str,
        page: playwright.async_api.Page,
        context,
        send_message_to_user: callable,
        report_infeasible_instructions: callable,
):
    """
    Executes Python code in a new context, including asynchronous code using `await`.

    Args:
        code: the Python code to execute, as a string.
        page: the playwright page that will be made accessible to the code.
        send_message_to_user: utility function that will be made accessible to the code.
        report_infeasible_instructions: utility function that will be made accessible to the code.
    """
    globals = {
        "page": page,
        "context": context,
        "send_message_to_user": send_message_to_user,
        "report_infeasible_instructions": report_infeasible_instructions,
    }

    # Format the code with proper indentation
    formatted_code = "\n".join("    " + line for line in code.splitlines())

    # Create the async function wrapper with the properly indented code
    wrapper = f"""async def __ex():
{formatted_code}"""

    # Execute the wrapped code
    exec_globals = {}
    exec(wrapper, globals, exec_globals)
    await exec_globals['__ex']()


