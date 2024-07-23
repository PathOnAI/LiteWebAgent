import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from dotenv import load_dotenv
import os, shutil, json

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

class ReaderAgent:
    def __init__(self):
        self.config =  {
                "temperature": 0.0,
                # "top_p": 0.95,
                # "top_k": 64,
                "max_output_tokens": 8192,
                "response_mime_type": "application/json",
            }
        

        self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config=self.config, safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        },
        system_instruction="""
        You are a user webpage tracker that is able to parse HTML content and output information about the given \
        webpage code in JSON format. The output should be a JSON object with the following format
        {
            name: 'Name of Webpage',
            description: 'Detailed description of the website, 1-2 paragraphs',
            venture_guess: 'Venture a guess at what the user could be doing on the website'
        }
        """
        )

    def read_schema(self, content: str):
        template = f"""
        Webpage HTML Content: {content}
        """

        response = self.model.generate_content(template)

        data = json.loads(response.text)

        self.write_webpage_info([data], 'data.txt')

    def clean_webpage_info(self, filename):
        """
        Appends a list of webpage info objects to a text file.
        
        :param webpage_info_list: List of dictionaries containing webpage info
        :param filename: Name of the file to write to
        """
        with open(filename, 'w+') as file:
            file.write('')

    def write_webpage_info(self, webpage_info_list, filename):
        """
        Appends a list of webpage info objects to a text file.
        
        :param webpage_info_list: List of dictionaries containing webpage info
        :param filename: Name of the file to write to
        """
        with open(filename, 'a') as file:
            for info in webpage_info_list:
                json_string = json.dumps(info)
                file.write(json_string + '\n')

    def read_webpage_info(self, filename):
        """
        Reads webpage info objects from a text file.
        
        :param filename: Name of the file to read from
        :return: List of dictionaries containing webpage info
        """
        webpage_info_list = []
        with open(filename, 'r') as file:
            for line in file:
                info = json.loads(line.strip())
                webpage_info_list.append(info)
        return webpage_info_list