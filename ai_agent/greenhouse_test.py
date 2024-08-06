from ai_agent.playwright_manager import get_browser, get_context, get_page, playwright_manager

from dotenv import load_dotenv
import playwright
_ = load_dotenv()
import time
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

from ai_agent.webagent import use_web_agent
from ai_agent.osagent import use_os_agent

def driver_main(q):
    start = time.time()
    output = main()
    end = time.time()
    runtime = end - start
    q.put((runtime, output))

def main():
    # goal = "enter the 'San Francisco' as destination"

    # page = get_page()
    # page.goto("https://job-boards.greenhouse.io/duolingo/jobs/7562886002?gh_src=81b1e41f2us")
    # tasks = [
    #     "(1) fill first name as Danqing",
    #     "(2) fill last name as Zhang",
    #     "(3) fill email address as dz@gmail.com",
    #     "(4) fill phone number as 6504506243",
    #     "(5) set location as San Francisco",
    #     "(6) click the first one in the dropdown list of location.",
    #     "(7) upload file /Users/danqingzhang/Desktop/SPC_hackathon/test_resume/Karen_Zhang.pdf",
    #     "(8) fill preferred first name as Danqing",
    #     "(9) submit application"
    # ]
    #
    # combined_tasks = "\n".join(tasks)
    # # for description in tasks:
    # response = use_browsergym_agent(combined_tasks)
    # print(response)


    # stage 1. pull information from the url
    # description = "download https://job-boards.greenhouse.io/uniswapfoundation/jobs/4459119007, extract the main content, save in ./playground/test/README.md file, "
    # response = use_os_agent(description)
    # print(response)
    #
    # ## stage 2, write a new markdown file based on information
    # description = "load original resume content from file ./test_resume/longREADME.md, and load the job description called ./playground/test/README.md, rewrite the resume based on job description and save the new resume called ./playground/test/updated_resume.md "
    # response = use_os_agent(description)
    # print(response)

    # ## stage 3, convert markdown file into pdf file
    # import os
    # import subprocess
    # def convert_markdown_to_pdf(input_file, output_file):
    #     # Ensure the input file exists
    #     if not os.path.exists(input_file):
    #         raise FileNotFoundError(f"Input file not found: {input_file}")
    #
    #     # Construct the pandoc command
    #     command = [
    #         "pandoc",
    #         input_file,
    #         "-o", output_file,
    #         "--pdf-engine=xelatex",
    #         "-V", "geometry:margin=1in"
    #     ]
    #
    #     # Run the pandoc command
    #     try:
    #         result = subprocess.run(command, check=True, capture_output=True, text=True)
    #         print(f"Successfully converted {input_file} to {output_file}")
    #         print(f"Pandoc output: {result.stdout}")
    #     except subprocess.CalledProcessError as e:
    #         print(f"Error converting file: {e}")
    #         print(f"Pandoc error output: {e.stderr}")
    #
    # # File paths
    # input_file = "./playground/test/updated_resume.md"
    # output_file = "./playground/test/updated_resume.pdf"
    #
    # # Run the conversion
    # convert_markdown_to_pdf(input_file, output_file)
    #
    #
    # stage 4. job application
    browser = get_browser()
    context = get_context()
    page = get_page()
    playwright_manager.playwright.selectors.set_test_id_attribute('data-unique-test-id')

    page.goto("https://job-boards.greenhouse.io/paveakatroveinformationtechnologies/jobs/4422780005")
    #page.goto("https://job-boards.greenhouse.io/uniswapfoundation/jobs/4459119007")
    tasks = [
        "(1) fill first name as Karen",
        "(2) fill last name as Zhang",
        "(3) fill email as kz@gmail.com",
        "(4) fill phone number as 650450000"
        "(5) upload resume file ./ai_agent/playground/test/updated_resume.pdf",
        # "(6) fill in location as San Francisco",
        # "(7) press tab",
        "(8) fill 'Do you now, or will you in the future, require sponsorship for employment visa status (e.g., H-1B visa status, etc.) to work legally for our Company in the United States?' as Yes",
        "(9) press tab",
        "(10) fill 'Pave believes in-person work is a key component in building a world-class culture and product. As such, we are seeking talent who can work in-office several times per week. Which office(s) are you applying for??' as San Francisco",
        "(11) press tab",
        "(12) submit application"
    ]

    # press('239', 'Tab')
    # combined_tasks = "\n".join(tasks)
    for description in tasks:
        response = use_web_agent(description)
        print(response)
    return response


if __name__ == "__main__":
    main()