from litewebagent.utils.utils import encode_image
from litewebagent.action.utils import prepare_prompt
from litewebagent.action.utils import build_highlevel_action_parser
from collections import defaultdict


def is_goal_finished(messages, openai_client):
    from pydantic import BaseModel
    class Plan(BaseModel):
        goal_finished: bool

    new_response = openai_client.beta.chat.completions.parse(
        model='gpt-4o-mini',
        messages=messages,
        response_format=Plan,
    )
    message = new_response.choices[0].message.parsed

    goal_finished = message.goal_finished
    return goal_finished


def extract_top_actions(trajectory, goal, page_info, action_set, openai_client, branching_factor):
    system_msg = f"""
            # Instructions
            Review the current state of the page and all other information to find the best
            possible next action to accomplish your goal. Your answer will be interpreted
            and executed by a program, make sure to follow the formatting instructions.
    
            Previous actions and action results are: {trajectory}
    
            Provide ONLY ONE action. Do not suggest multiple actions or a sequence of actions.
            # Goal:
            {goal}"""

    prompt = prepare_prompt(page_info, action_set, 'axtree')
    base64_image = encode_image(page_info['screenshot'])

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_msg},
            {"role": "user",
             "content": [
                 {"type": "text", "text": prompt},
                 {"type": "image_url",
                  "image_url": {
                      "url": f"data:image/jpeg;base64,{base64_image}",
                      "detail": "high"
                  }
                  }
             ]
             },
        ],
        n=max(branching_factor * 2, 20)
    )
    responses: list[str] = [x.message.content for x in response.choices]
    highlevel_action_parser = build_highlevel_action_parser()
    print(responses)
    parsed_actions_count = defaultdict(int)
    all_actions = {}
    for response in responses:
        result = highlevel_action_parser.parse_string(response)
        result = result[0] if result else ""  # Convert to string
        if result not in all_actions:
            all_actions[result] = {'action': response}
        parsed_actions_count[result] += 1
    print(parsed_actions_count)
    top_actions = sorted(parsed_actions_count, key=parsed_actions_count.get, reverse=True)[:branching_factor]
    top_action_count = sum([parsed_actions_count[action] for action in top_actions])
    updated_actions = []
    for action in top_actions:
        a = all_actions[action]
        a['prob'] = parsed_actions_count[action] / top_action_count
        updated_actions.append(a)
    return updated_actions
