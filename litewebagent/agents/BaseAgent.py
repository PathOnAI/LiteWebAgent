import json
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self, model_name, tools, available_tools, messages, goal):
        self.model_name = model_name
        self.tools = tools
        self.available_tools = available_tools
        self.messages = messages
        self.goal = goal
        self.messages.append({"role": "user", "content": "The goal is:{}".format(self.goal)})

    def process_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        tool_call_responses = []
        logger.info("Number of function calls: %i", len(tool_calls))
        for tool_call in tool_calls:
            tool_call_id = tool_call["id"]
            function_name = tool_call["function"]["name"]
            function_args = json.loads(tool_call["function"]["arguments"])

            function_to_call = self.available_tools.get(function_name)

            def make_tool_response_message(response):
                return {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "name": function_name,
                    "content": str(response),
                }

            function_response = None
            try:
                function_response = function_to_call(**function_args)
                logger.info('function name: %s, function args: %s', function_name, function_args)
                logger.info('function name: %s, function response %s', function_name, str(function_response))
            except Exception as e:
                logger.error(f"Error while calling function <{function_name}>: {e}")
            finally:
                tool_call_responses.append(make_tool_response_message(function_response))

        return tool_call_responses

    def send_completion_request(self, plan: str, depth: int = 0) -> Dict:
        raise NotImplementedError("This method should be implemented by subclasses")

    def send_prompt(self, plan: str) -> Dict:
        self.messages.append({"role": "user", "content": "The plan is: {}".format(plan)})
        plan = plan
        return self.send_completion_request(plan, 0)