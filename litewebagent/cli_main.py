import sys
import json
import time
from litewebagent.playwright_manager import PlaywrightManager, get_browser, get_context, get_page, close_playwright, playwright_manager
from dotenv import load_dotenv
import argparse
_ = load_dotenv()
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("log.txt", mode="w"),
        logging.StreamHandler()
    ]
)

# Create a logger
logger = logging.getLogger(__name__)

from litewebagent.webagent import setup_web_agent

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
    try:
        # Initialize PlaywrightManager (it's already a global instance in your setup)
        browser = get_browser()
        context = get_context()
        page = playwright_manager.get_page()
        playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

        # Get initial setup from user
        starting_url = input("Enter the starting URL: ")
        goal = input("Enter the goal: ")
        plan = input("Enter the initial plan: ")

        # Setup the web agent
        agent = setup_web_agent(starting_url, goal, model_name=args.model, agent_type=args.agent_type)
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

    finally:
        # Cleanup
        close_playwright()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Web Agent CLI")
    parser.add_argument('--agent_type', type=str, default="DemoAgent",
                        choices=["DemoAgent", "HighLevelPlanningAgent"],
                        help="Type of agent to use (default: DemoAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    args = parser.parse_args()

    main(args)