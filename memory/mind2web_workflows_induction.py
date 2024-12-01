"""Induce Website-Specific Workflows Offline from Training Examples."""

import os
import json
import argparse

from openai import OpenAI
client = OpenAI()

def induce_single_website(data_dict, website: str, output_dir: str, **kwargs):
    """Pipeline to induce, filter, and save workflows on a single website."""
    examples = get_examples(data_dict, website)
    print(f"Split {website} with #{len(examples)} examples")
    response = llm_generate(website, examples, **kwargs)
    workflows = filter_workflows(response, website)
    save_log(workflows, "workflows")
    save_to_txt(workflows, output_dir, website)

def llm_generate(website: str, examples: list[dict], model_name: str, temperature: float,
                 instruction: str, one_shot: str, verbose: bool):
    """Call gpt model to generate workflows."""
    system_prompt = '\n\n'.join([instruction, one_shot])
    user_prompt = f"## Website: {website} \n"
    user_prompt += format_examples(examples)
    save_log(f"SYSTEM PROMPT: \n{system_prompt}\n\nUSER PROMPT: \n{user_prompt}", "prompt")
    if verbose: 
        print("System prompt:\n", system_prompt, '\n\n')
        print("User prompt:\n", user_prompt, '\n\n')
    response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
            temperature=temperature,
            max_tokens=1024,
    )
    response = response.choices[0].message.content
    save_log(response, "response")
    if verbose: print(response)
    return response

def get_data_dict(paths: list[str]) -> dict:
    """Create dict for examples in domain-subdomain-website hierarchy.
    Args:
        paths: list[str], list of data path strings
    Rets:
        data_dict: dict[str, dict], (domain, subdomain, website) dict
    """
    print("Start loading data files...")
    data_dict = {}
    for p in paths:
        data = json.load(open(p, 'r', encoding='utf-8'))
        for ex in data:
            website = ex["website"]
            if website not in data_dict:
                data_dict[website] = []
            data_dict[website].append(ex)
    print(f"Finished loading {len(paths)} files!")
    return data_dict

def get_examples(data_dict: dict, website: str) -> list[dict]:
    return data_dict[website]

def format_examples(examples: list[dict]) -> str:
    lines = []
    for i, ex in enumerate(examples):
        lines.append(f"Query {i+1}: {ex['confirmed_task']}")
        lines.append("Actions:")
        lines.extend(ex["action_reprs"])
        lines.append("")
    prompt = '\n'.join(lines)
    prompt += '\n\n' + "## Summary Workflows:\n"
    return prompt

def filter_workflows(text: str, website: str) -> str:
    return text

def save_to_txt(text: str, output_dir: str, website: str):
    """Save text to a .txt file."""
    with open(get_output_path(output_dir, website), 'w', encoding='utf-8') as fw:
        fw.write(text)

def get_output_path(output_dir: str, website: str):
    output_name = f"{website.lower()}.txt"
    output_path = os.path.join(output_dir, output_name)
    return output_path

def save_log(text: str, name):
    log_dir = "memory/log/"
    os.makedirs(log_dir, exist_ok=True)
    with open(f'{log_dir}/{name}.txt', 'w', encoding='utf-8') as fw:
        fw.write(text)

def main():
    output_dir = "memory/workflow"
    instruction_path = "memory/prompt/instruction_action.txt"
    oneshot_path = "memory/prompt/one_shot_action.txt"

    INSTRUCTION = open(instruction_path, "r", encoding='utf-8').read()
    ONE_SHOT = open(oneshot_path, "r", encoding='utf-8').read()

    data_dir, websites, model_name, temperature, verbose, skip = \
        args.data_dir, args.websites, args.model_name, args.temperature, args.verbose, args.skip

    data_paths = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
    data_dict = get_data_dict(paths=data_paths)

    for website in websites:
        if skip and os.path.exists(get_output_path(output_dir, website)):
            print(f'Skip {website}!')
            continue

        induce_single_website(data_dict, website, model_name=model_name, temperature=temperature, 
            instruction=INSTRUCTION, one_shot=ONE_SHOT, output_dir=output_dir, verbose=verbose)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--websites", type=str, default=None,
                        help="Comma seperated website names.")
    parser.add_argument("--data_dir", type=str, default="memory/mind2web/train")

    # model
    parser.add_argument("--model_name", type=str, default="gpt-4o")
    parser.add_argument("--temperature", type=float, default=0.0)

    parser.add_argument("--verbose", default="False", 
                        help="Whether to print prompt and response.")

    parser.add_argument("--skip", default="True", 
                        help="Whether to skip induced workflows.")
    
    args = parser.parse_args()
    args.websites = args.websites.split(',')

    main()
