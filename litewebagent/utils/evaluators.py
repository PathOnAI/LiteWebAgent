from pydantic import BaseModel
import math

class Plan(BaseModel):
    goal_finished: bool

def parse_oai_logprob(response):
    response_logprob = 0
    try:
        for content in response.choices[0].logprobs.content:
            response_logprob += content.logprob
        return round(math.exp(response_logprob),5)
    except Exception as e:
        print(f"An error occurred when checking oai logprob: {e}") 


def goal_finished_evaluator(messages, openai_client):    
    new_response = openai_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=Plan,
        logprobs=True,        
    )
    message = new_response.choices[0].message.parsed
    score = parse_oai_logprob(new_response)

    goal_finished = message.goal_finished
    return goal_finished, score


# def goal_finished_value_function():
    # pass

def early_stop(
    trajectory: list, action_set: dict, max_steps: int, score_thresholds: dict[str, int]
) -> tuple[bool, str]:
    """Check whether need to stop early"""

    # reach the max step
    num_steps = (len(trajectory) - 1) / 2
    if num_steps >= max_steps:
        return True, f"Reach max steps {max_steps}"

    last_k_actions: list[Action]
    action_seq: list[Action]

    # Case: parsing failure for k times
    
    # Case: same action for k times
    pass