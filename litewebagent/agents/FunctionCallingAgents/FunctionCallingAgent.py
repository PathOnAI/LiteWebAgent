from litellm import completion
from .BaseAgent import BaseAgent
from typing import Dict
import logging

logger = logging.getLogger(__name__)


# very basic recursive function calling
class FunctionCallingAgent(BaseAgent):
    def send_completion_request(self, plan: str, depth: int = 0, emitter=None) -> Dict:
        if plan is None and depth == 0:
            plan = self.make_plan()
            self.messages.append({"role": "user", "content": "The plan is: {}".format(plan)})
        if depth >= 8:
            return "max depth reached, agent stops execution"
        logger.info("plan is %s", plan)

        if not self.tools:
            response = completion(model=self.model_name, messages=self.messages)
            logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                        str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
            logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response.choices[0].message.content

        response = completion(model=self.model_name, messages=self.messages, tools=self.tools, tool_choice="auto")

        logger.info('agent: %s, prompt tokens: %s, completion tokens: %s', self.model_name,
                    str(response.usage.prompt_tokens), str(response.usage.completion_tokens))
        logger.info('agent: %s, depth: %s, response: %s', self.model_name, depth, response)

        if hasattr(response.choices[0].message, 'tool_calls'):
            tool_calls = response.choices[0].message.tool_calls
        else:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response.choices[0].message.content

        if tool_calls is None or len(tool_calls) == 0:
            message = response.choices[0].message.model_dump()
            self.messages.append(message)
            return response.choices[0].message.content

        tool_call_message = {"content": response.choices[0].message.content,
                             "role": response.choices[0].message.role,
                             "tool_calls": tool_calls}

        self.messages.append(tool_call_message)
        tool_responses = self.process_tool_calls(tool_calls)
        
        if emitter:
            emitter(tool_responses)

        self.messages.extend(tool_responses)

        return self.send_completion_request(plan, depth + 1, emitter)
