from dotenv import load_dotenv
import argparse

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.utils.playwright_manager import setup_playwright

def main(args):
    # Use the features from command-line arguments
    features = args.features.split(',') if args.features else None
    branching_factor = args.branching_factor if args.branching_factor else None

    # Use the tool_names from command-line arguments
    tool_names = args.tool_names.split(',') if args.tool_names else ["navigation", "select_option", "upload_file", "webscraping"]

    playwright_manager = setup_playwright(log_folder=args.log_folder, storage_state=None, headless=False)
    agent = setup_function_calling_web_agent(starting_url=args.starting_url, goal=args.goal, playwright_manager=playwright_manager, model_name=args.model, agent_type=args.agent_type,
                            features=features, tool_names=tool_names, branching_factor=branching_factor, log_folder=args.log_folder)

    response = agent.send_prompt(args.plan)
    print(response)
    print(agent.messages)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="FunctionCallingAgent",
                        choices=["FunctionCallingAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent"],
                        help="Type of agent to use (default: FunctionCallingAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--starting_url', type=str, required=True,
                        help="Starting URL for the web automation task")
    parser.add_argument('--plan', type=str, required=True,
                        help="Plan for the web automation task")
    parser.add_argument('--goal', type=str, required=True,
                        help="Goal for the web automation task")
    parser.add_argument('--storage_state', type=str, default="state.json",
                        help="Storage state json file")
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: axtree)")
    parser.add_argument('--tool_names', type=str, default="navigation,select_option,upload_file,webscraping",
                        help="Comma-separated list of tool names to use (default: navigation,select_option,upload_file,webscraping)")
    parser.add_argument('--branching_factor', type=int, default=None)
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    args = parser.parse_args()
    main(args)
