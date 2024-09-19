# copied and modified from https://github.com/ServiceNow/BrowserGym
import playwright.sync_api
from abc import ABC, abstractmethod


def execute_python_code(
    code: str,
    page: playwright.sync_api.Page,
    context,
    send_message_to_user: callable,
    report_infeasible_instructions: callable,
):
    """
    Executes Python code in a new context, except for a playwright `page` object and a `send_message_to_user` function.

    WARNING: this is not safe!
    https://stackoverflow.com/questions/77655440/can-you-protect-a-python-variable-with-exec

    Args:
        code: the Python code to execute, as a string.
        page: the playwright page that will be made accessible to the code.
        send_message_to_user: utility function that will be made accessible to the code. It should take one text argument.
        report_infeasible_instructions: utility function that will be made accessible to the code. It should take one text argument.
    """

    globals = {
        "page": page,
        "context": context,
        "send_message_to_user": send_message_to_user,
        "report_infeasible_instructions": report_infeasible_instructions,
    }

    exec(code, globals)
