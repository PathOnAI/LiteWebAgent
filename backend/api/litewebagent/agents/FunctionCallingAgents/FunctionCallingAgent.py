from litellm import completion
from .BaseAgent import BaseAgent
from typing import Dict
import logging

logger = logging.getLogger(__name__)


# very basic chain of thought by providing the message list to OpenAI API


class FunctionCallingAgent(BaseAgent):
    async def send_completion_request(self, plan: str, depth: int = 0, emitter=None) -> Dict:
        if plan is None and depth == 0:
            plan = self.make_plan()
            if emitter:
                await emitter({
                    "type": "plan",
                    "message": f"Plan generated: {plan}"
                })

        if depth >= 8:
            if emitter:
                await emitter({
                    "type": "warning",
                    "message": "Maximum recursion depth reached"
                })
            return None

        try:
            # Get model response
            if not self.tools:
                response = completion(
                    model=self.model_name,
                    messages=self.messages
                )
                if emitter:
                    await emitter({
                        "type": "completion",
                        "message": response.choices[0].message.content
                    })
                message = response.choices[0].message.model_dump()
                self.messages.append(message)
                return response

            response = completion(
                model=self.model_name,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto"
            )

            # Emit thinking state
            if emitter:
                await emitter({
                    "type": "thinking",
                    "message": response.choices[0].message.content or "Processing next step..."
                })

            print('aaaaaadsfsdfdsfsfsdfs')

            # Handle tool calls
            tool_calls = getattr(response.choices[0].message, 'tool_calls', None)
            if not tool_calls:
                message = response.choices[0].message.model_dump()
                self.messages.append(message)
                if emitter:
                    await emitter({
                        "type": "action",
                        "message": "No actions needed"
                    })
                return response

            # Process tool calls
            tool_call_message = {
                "content": response.choices[0].message.content,
                "role": response.choices[0].message.role,
                "tool_calls": tool_calls
            }
            self.messages.append(tool_call_message)

            if emitter:
                await emitter({
                    "type": "tool_calls",
                    "message": f"Executing {len(tool_calls)} actions..."
                })

            print('aaaaaasdfsfddsfsdfdsfsfsdfs')

            # Process each tool call and emit results
            for tool_call in tool_calls:
                if emitter:
                    await emitter({
                        "type": "tool_execution",
                        "message": f"Executing: {tool_call.function.name}"
                    })
                    
            tool_responses = await self.process_tool_calls(tool_calls)
            
            for response in tool_responses:
                if emitter:
                    await emitter({
                        "type": "tool_result",
                        "message": response
                    })

            self.messages.extend(tool_responses)
            
            # Continue processing
            return await self.send_completion_request(plan, depth + 1, emitter)

        except Exception as e:
            if emitter:
                await emitter({
                    "type": "error",
                    "message": f"Error during execution: {str(e)}"
                })
            raise
