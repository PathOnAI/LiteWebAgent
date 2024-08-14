from litellm import completion
from .BaseAgent import BaseAgent
from typing import List, Dict, Any
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv
import os
_ = load_dotenv()

client = OpenAI()

logger = logging.getLogger(__name__)

class HighLevelPlanningAgent(BaseAgent):
    def send_completion_request(self, messages: List[Dict], plan: str, depth: int = 0) -> Dict:
        if depth >= 8:
            return None

        if not self.tools:
            response = completion(model=self.model_name, messages=messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            messages.append(message)
            return response

        logger.info("last message: %s", json.dumps(messages[-1]))
        logger.info('current plan: %s', plan)

        from pydantic import BaseModel
        class Plan(BaseModel):
            task_finished: bool
            updated_plan: str
            completed_tasks: str

        if depth > 0:
            prompt = """
            Current plan: {}

            Based on the progress made so far, please provide:

            1. An updated complete plan
            2. A list of tasks that have already been completed
            3. An explanation of changes and their rationale

            Format your response as follows:

            Updated Plan:
            - [Step 1]
            - [Step 2]
            - ...

            Completed Tasks:
            - [Task 1]
            - [Task 2]
            - ...
            """.format(plan)
            messages.append({"role": "user", "content": prompt})
            response = client.beta.chat.completions.parse(model=self.model_name, messages=messages, response_format=Plan)
            message = response.choices[0].message.parsed
            updated_plan = message.updated_plan
            completed_tasks = message.completed_tasks
            logger.info('Replan: %s', message)
            if message.task_finished:
                return response
            else:
                combined_str = "updated plan is: {}, completed tasks are: {}".format(updated_plan, completed_tasks)
                messages.append({"role": "assistant", "content": combined_str})


        logger.info('updated plan: %s', plan)
        response = completion(model=self.model_name, messages=messages, tools=self.tools, tool_choice="auto")

        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
        tool_calls = response.choices[0].message.tool_calls

        if tool_calls is None or len(tool_calls) == 0:
            message = response.choices[0].message.model_dump()
            messages.append(message)
            return response
        # limit one function calling at a time
        tool_calls = [tool_calls[0]]

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        messages.extend(tool_responses)

        return self.send_completion_request(messages, plan, depth + 1)