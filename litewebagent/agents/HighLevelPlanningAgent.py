from litellm import completion
from .BaseAgent import BaseAgent
from typing import List, Dict, Any
import json
import logging

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

        if depth > 0:
            prompt = """
            Current plan: {}

            Based on the progress made so far, please provide:

            1. An updated complete plan
            2. A list of tasks that have already been completed
            3. The next task to be tackled
            4. An explanation of changes and their rationale

            Format your response as follows:

            Updated Plan:
            - [Step 1]
            - [Step 2]
            - ...

            Completed Tasks:
            - [Task 1]
            - [Task 2]
            - ...

            Next Task:
            [Specify the next task to be done]
            """.format(plan)
            messages.append({"role": "user", "content": prompt})
            response = completion(model=self.model_name, messages=messages, tools=self.tools, tool_choice="auto")
            message = response.choices[0].message.model_dump()
            plan = message['content']
            messages.append(message)


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

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        messages.extend(tool_responses)

        return self.send_completion_request(messages, plan, depth + 1)