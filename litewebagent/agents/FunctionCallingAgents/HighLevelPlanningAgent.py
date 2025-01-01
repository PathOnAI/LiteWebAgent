from litellm import completion
from .BaseAgent import BaseAgent
from typing import Dict
import json
import logging
from openai import OpenAI
from dotenv import load_dotenv

_ = load_dotenv()

openai_client = OpenAI()

logger = logging.getLogger(__name__)


class HighLevelPlanningAgent(BaseAgent):
    def send_completion_request(self, plan: str, depth: int = 0, emitter=None) -> Dict:
        if plan is None and depth == 0:
            plan = self.make_plan()
            self.messages.append({"role": "user", "content": "The plan is: {}".format(plan)})
        if depth >= 8:
            return None

        if not self.tools:
            response = completion(model=self.model_name, messages=self.messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        logger.info("last message: %s", json.dumps(self.messages[-1]))
        logger.info('current plan: %s', plan)

        if depth > 0:
            from pydantic import BaseModel
            class Plan(BaseModel):
                goal_finished: bool

            prompt = """
            Goal: {}
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
            """.format(self.goal, plan)
            self.messages.append({"role": "user", "content": prompt})
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=self.messages
            )
            plan = response.choices[0].message.content
            new_response = openai_client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[{"role": "system", "content": "Is the overall goal finished?"},
                          {"role": "user", "content": plan}],
                response_format=Plan
            )
            message = new_response.choices[0].message.parsed
            goal_finished = message.goal_finished
            if goal_finished:
                logger.info("goal finished")
                return response
            else:
                self.messages.append({"role": "user", "content": plan})

        logger.info('updated plan: %s', plan)
        response = completion(model=self.model_name, messages=self.messages, tools=self.tools, tool_choice="auto")

        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)

        if hasattr(response.choices[0].message, 'tool_calls'):
            tool_calls = response.choices[0].message.tool_calls
        else:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response

        if tool_calls is None or len(tool_calls) == 0:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response
        # limit one function calling at a time
        tool_calls = [tool_calls[0]]

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        self.messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        self.messages.extend(tool_responses)

        return self.send_completion_request(plan, depth + 1, emitter=None)
