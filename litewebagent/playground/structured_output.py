from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
_ = load_dotenv()
client = OpenAI()

class CalendarEvent(BaseModel):
    name: str
    date: str
    participants: list[str]

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Extract the event information."},
        {"role": "user", "content": "Alice and Bob are going to a science fair on Friday."},
    ],
    response_format=CalendarEvent,
)

event = completion.choices[0].message.parsed
print(event)


class Plan(BaseModel):
    task_finished: bool
    updated_plan: str

completion = client.beta.chat.completions.parse(
    model="gpt-4o-2024-08-06",
    messages=[
        {"role": "system", "content": "Update the plan"},
        {"role": "user", "content": "(1) enter the 'San Francisco' as destination, (2) and click search"},
    ],
    response_format=Plan,
)

plan = completion.choices[0].message.parsed
print(plan)
print(plan.task_finished)