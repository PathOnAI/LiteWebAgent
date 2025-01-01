from dotenv import load_dotenv
import argparse

_ = load_dotenv()
from litewebagent.core.agent_factory import setup_function_calling_web_agent
from litewebagent.webagent_utils_sync.utils.playwright_manager import setup_playwright
import json
from PIL import Image
import requests
from evaluation_suite import evaluator_router, image_utils
## first make it work for function calling agent
## load json config file
## add evaluate suite to evaluate agent performance

def main(args):
    # Use the features from command-line arguments
    features = args.features.split(',') if args.features else None
    branching_factor = args.branching_factor if args.branching_factor else None

    # Use the tool_names from command-line arguments
    tool_names = args.tool_names.split(',') if args.tool_names else ["navigation", "select_option", "upload_file", "webscraping"]
    config_file = args.config_file
    print(config_file)

    ## log confile file
    with open(config_file) as f:
        _c = json.load(f)
        goal = _c["intent"]
        task_id = _c["task_id"]
        starting_url = _c["start_url"]
        storage_state = _c["storage_state"]
        image_paths = _c.get("image", None)
        images = []


        if image_paths is not None:
            if isinstance(image_paths, str):
                image_paths = [image_paths]
            for image_path in image_paths:
                # Load image either from the web or from a local path.
                if image_path.startswith("http"):
                    input_image = Image.open(requests.get(image_path, stream=True).raw)
                else:
                    input_image = Image.open(image_path)

                images.append(input_image)


        print(f"[Config file]: {config_file}")
        print(f"[Goal]: {goal}")
        print(f"[Starting Url]: {starting_url}")
        print(f"[Storage State]: {storage_state}")
        print(f"[Task id]: {task_id}")
        print(len(images))
    

    playwright_manager = setup_playwright(storage_state=storage_state, headless=False)
    agent = setup_function_calling_web_agent(starting_url=starting_url, goal=goal, playwright_manager=playwright_manager, model_name=args.model, agent_type=args.agent_type,
                            features=features, elements_filter=args.elements_filter,tool_names=tool_names, branching_factor=branching_factor, log_folder=args.log_folder, workflow_memory_website=args.workflow_memory_website)

    response = agent.send_prompt(goal)
    print(response)
        # NOTE: eval_caption_image_fn is used for running eval_vqa functions.
    evaluator = evaluator_router(
        config_file, captioning_fn=None
    )
    score = evaluator(
        trajectory=[],
        config_file=config_file,
        page=playwright_manager.page
    )
    print(score)
    #print(agent.messages)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run web automation tasks with different agent types.")
    parser.add_argument('--agent_type', type=str, default="FunctionCallingAgent",
                        choices=["FunctionCallingAgent", "HighLevelPlanningAgent", "ContextAwarePlanningAgent"],
                        help="Type of agent to use (default: FunctionCallingAgent)")
    parser.add_argument('--model', type=str, default="gpt-4o-mini",
                        help="Model to use for the agent (default: gpt-4o-mini)")
    parser.add_argument('--features', type=str, default="axtree",
                        help="Comma-separated list of features to use (default: axtree, which uses accessibility tree)")  
    parser.add_argument('--elements_filter', type=str, default="none",
                    choices=["som", "visibility", "none"],
                    help="Filter for dom elements"
                    )
    parser.add_argument('--tool_names', type=str, default="navigation,select_option,upload_file,webscraping",
                        help="Comma-separated list of tool names to use (default: navigation,select_option,upload_file,webscraping)")
    parser.add_argument('--branching_factor', type=int, default=None)
    parser.add_argument('--log_folder', type=str, default='log', help='Path to the log folder')
    parser.add_argument('--config_file', type=str, default='evaluation_suite/configs/196.json', help='Path to the config file')
    parser.add_argument('--workflow_memory_website', type=str, default=None, help='Website name for filtering memory')
    args = parser.parse_args()
    main(args)
