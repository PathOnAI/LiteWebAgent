from litellm import completion
from .BaseAgent import BaseAgent
from typing import List, Dict, Any
import json
import logging

logger = logging.getLogger(__name__)

class ReActAgent(BaseAgent):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.plan_max_fail_times = 3
        self.tool_call_max_fail_times = 3

    def check_workflow(self, message):
        try:
            # print(f"Workflow message: {message}")
            workflow = json.loads(message)
            if not isinstance(workflow, list):
                return None

            for step in workflow:
                if "message" not in step or "tool_use" not in step:
                    return None

            return workflow

        except json.JSONDecodeError:
            return None

    def automatic_workflow(self):
        for i in range(self.plan_max_fail_times):
            response = self.get_response(
                query = Query(
                    messages = self.messages,
                    tools = None,
                    message_return_type="json"
                )
            )


            workflow = self.check_workflow(response.response_message)

            self.rounds += 1

            if workflow:
                return workflow

            else:
                self.messages.append(
                    {
                        "role": "assistant",
                        "content": f"Fail {i+1} times to generate a valid plan. I need to regenerate a plan"
                    }
                )
        return None

    def send_completion_request(self, plan: str | None, depth: None = None) -> Dict:
        if plan is None:
            plan = self.make_plan()
