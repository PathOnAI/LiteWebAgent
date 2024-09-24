import sys
import json
import time
from litewebagent.utils.playwright_manager import PlaywrightManager
from dotenv import load_dotenv
import argparse
import os
_ = load_dotenv()
from litewebagent.utils.utils import setup_logger
from litewebagent.agents.webagent import setup_web_agent

def progress_indicator():
    chars = '|/-\\'
    i = 0
    while True:
        yield chars[i]
        i = (i + 1) % len(chars)

def display_output_cli(output):
    if output["type"] == "console":
        print(output["content"])
    else:
        print(json.dumps(output, indent=2))

def main(args):
    log_folder = args.log_folder
    logger = setup_logger(log_folder)
    # Initialize PlaywrightManager (it's already a global instance in your setup)
    playwright_manager = PlaywrightManager(storage_state="state.json", video_dir=os.path.join(args.log_folder, 'videos'))
    browser = playwright_manager.get_browser()
    context = playwright_manager.get_context()
    page = playwright_manager.get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')
    features = args.features.split(',') if args.features else None
    branching_factor = args.branching_factor if args.branching_factor else None

    # Get initial setup from user
    starting_url = input("Enter the starting URL: ")
    goal = input("Enter the goal: ")
    plan = input("Enter the initial plan: ")

    # Setup the web agent
    agent = setup_web_agent(starting_url, goal, model_name=args.model, agent_type=args.agent_type, features=features, branching_factor=branching_factor, playwright_manager=playwright_manager , log_folder=args.log_folder)
    # Initial agent response
    print("\n[Agent]: Initializing with the provided plan...")
    spinner = progress_indicator()
    try:
        response = agent.send_prompt(plan)
        sys.stdout.write('\r')  # Clear the spinner
        sys.stdout.flush()
        print("[Agent]: The response is as follows: ")
        output = {"type": "console", "content": response}
        display_output_cli(output)
    except Exception as e:
        print(f"[Agent]: An error occurred: {str(e)}")
    finally:
        sys.stdout.write('\r')  # Clear the spinner
        sys.stdout.flush()

    # Main interaction loop
    while True:
        user_input = input("\n[User]: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            print("[Agent]: Goodbye!")
            sys.exit(0)  # Immediately exit the process

        spinner = progress_indicator()
        try:
            for _ in range(100):  # Limit the spinner to avoid infinite loop
                sys.stdout.write(f'\r[Agent]: Thinking {next(spinner)}')
                sys.stdout.flush()
                time.sleep(0.1)
                response = agent.send_prompt(user_input)
                if response:
                    break
            sys.stdout.write('\r')  # Clear the spinner
            sys.stdout.flush()
            print("[Agent]: The response is as follows: ")
            output = {"type": "console", "content": response}
            display_output_cli(output)
        except Exception as e:
            print(f"[Agent]: An error occurred: {str(e)}")
        finally:
            sys.stdout.write('\r')  # Clear the spinner
            sys.stdout.flush()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Agent CLI")
    parser.add_argument('--agent_type', type=str, default="FunctionCallingAgent",
                        choices=["FunctionCallingAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent", "PromptSearchAgent", "PromptAgent"],
                        help="Type of agent to use (default: FunctionCallingAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: None, which uses all features)")
    parser.add_argument('--branching_factor', type=int, default=None)
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    args = parser.parse_args()

    main(args)