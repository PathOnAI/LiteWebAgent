from typing import Any
from pydantic import BaseModel, validator
import logging
import logging
from dotenv import load_dotenv
from openai import OpenAI
import subprocess
from typing import Any
from pydantic import BaseModel, validator
import requests
import os
import json
from litellm import completion
# Initialize logging
import logging
# Get a logger for this module
logger = logging.getLogger(__name__)
from litewebagent.config import agent_to_model


def process_tool_calls(tool_calls, available_tools):
    tool_call_responses = []
    logger.info("Number of function calls: %i", len(tool_calls))
    for tool_call in tool_calls:
        tool_call_id = tool_call["id"]
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])

        function_to_call = available_tools.get(function_name)

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



def send_completion_request(model_name, messages: list, tools: list = None, available_tools: dict = None, depth: int = 0) -> dict:
    print(messages)
    if depth >= 8:
        return None

    if tools is None:
        response = completion(
            model=model_name, messages=messages
        )
        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', agent_name, depth, response)
        message = response.choices[0].message.model_dump()
        messages.append(message)
        return response


    response = completion(
        model=model_name, messages=messages, tools=tools, tool_choice="auto"
    )


    logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', model_name, str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
    logger.info('agent: %s, depth: %s, response: %s', model_name, depth, response)
    tool_calls = response.choices[0].message.tool_calls

    if tool_calls is None or len(tool_calls) == 0:
        message = response.choices[0].message.model_dump()
        messages.append(message)
        return response

    tool_calls = response.choices[0].message.tool_calls

    tool_call_message = {"content": response.choices[0].message.content, "role": response.choices[0].message.role, "tool_calls": tool_calls}

    messages.append(tool_call_message)
    tool_responses = process_tool_calls(tool_calls, available_tools)
    messages.extend(tool_responses)

    return send_completion_request(model_name, messages, tools, available_tools, depth + 1)



def send_prompt(model_name, messages, content: str, tools, available_tools):
    messages.append({"role":"user", "content":content})
    return send_completion_request(model_name,  messages, tools, available_tools, 0)