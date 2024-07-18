import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

import os, shutil
from playwright.async_api import Page

from dotenv import load_dotenv

import random
import string
import asyncio
import re

load_dotenv()

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

generate_random_string = lambda: ''.join(random.choice(string.ascii_letters ) for _ in range(6))

remove_extra_newlines = lambda text: re.sub(r'\n\s*\n', '\n', text)

def remove_comment_lines(text: str):
    cleaned_lines = [line for line in text.splitlines() if not line.strip().startswith('<!--')]
    
    return '\n'.join(cleaned_lines)

def clean_text(t: str):
    t = remove_extra_newlines(t)
    t = remove_comment_lines(t)

    return t

def clear_directory(directory_path):
    # Check if the directory exists
    if not os.path.exists(directory_path):
        return

    # Iterate over all files and subdirectories
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                # Remove the file
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                # Remove the directory and its contents
                shutil.rmtree(file_path)
        except Exception as e:
            pass

class ScreenAgent:
    def __init__(self, host_page: Page, path: str = 'cache'):
        self.config =  {
            "temperature": 0.0,
            # "top_p": 0.95,
            # "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }

        self.model = genai.GenerativeModel('gemini-1.5-flash', generation_config=self.config, safety_settings={
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        })

        # self.function_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{path}.py'
        self.function_root = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/'
        self.webpage_path = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/{path}.txt'

        clear_directory(f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache')

        self.current_url: str = ''
        self.page = host_page

    def set_url(self, p: str):
        self.current_url = p
        return self
    
    async def read_page(self, navigate=False):
        if navigate:
            await self.page.goto(self.current_url, wait_until='domcontentloaded')
            self.current_url = self.page.url

        self.current_url = self.page.url

        try:
            main_content = await self.page.evaluate('''() => {
                let main = document.querySelector('main');
                if (!main) {
                    main = document.body;  
                }
                
                const clone = main.cloneNode(true);

                const unwantedTags = ['script', 'style', 'link', 'meta', 'noscript', 'iframe'];
                unwantedTags.forEach(tag => {
                    clone.querySelectorAll(tag).forEach(el => el.remove());
                });
                                                    
                clone.querySelectorAll('svg').forEach(svg => {
                    while (svg.firstChild) {
                        svg.removeChild(svg.firstChild);
                    }
                });

                // Remove data- attributes and limit classes to 3
                clone.querySelectorAll('*').forEach(el => {
                    [...el.attributes].forEach(attr => {
                        if (attr.name.startsWith('data-')) {
                            el.removeAttribute(attr.name);
                        } else if (attr.name === 'class') {
                            let classes = attr.value.split(/\s+/);
                            if (classes.length > 3) {
                                el.className = classes.slice(0, 3).join(' ');
                            }
                        }
                    });
                });

                return clone.innerHTML;
            }''')

            with open(self.webpage_path, 'w+', encoding="utf-8") as f:
                f.write(clean_text(main_content))

        except:
            await asyncio.sleep(4)

            main_content = await self.page.evaluate('''() => {
                let main = document.querySelector('main');
                if (!main) {
                    main = document.body;  
                }
                
                const clone = main.cloneNode(true);

                const unwantedTags = ['script', 'style', 'link', 'meta', 'noscript', 'iframe'];
                unwantedTags.forEach(tag => {
                    clone.querySelectorAll(tag).forEach(el => el.remove());
                });
                                                    
                clone.querySelectorAll('svg').forEach(svg => {
                    while (svg.firstChild) {
                        svg.removeChild(svg.firstChild);
                    }
                });

                // Remove data- attributes and limit classes to 3
                clone.querySelectorAll('*').forEach(el => {
                    [...el.attributes].forEach(attr => {
                        if (attr.name.startsWith('data-')) {
                            el.removeAttribute(attr.name);
                        } else if (attr.name === 'class') {
                            let classes = attr.value.split(/\s+/);
                            if (classes.length > 3) {
                                el.className = classes.slice(0, 3).join(' ');
                            }
                        }
                    });
                });

                return clone.innerHTML;
            }''')

            with open(self.webpage_path, 'w+', encoding="utf-8") as f:
                f.write(clean_text(main_content))
        finally:
            await self.page.screenshot(path=f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/snapshot.png', full_page=True)
        return self
    
    def _remove_code_markers(self, text: str):
        if text.startswith("```python\n"):
            text = text[10:]
        if text.endswith("\n```"):
            text = text[:-4]
        return text
    
    
    async def build_action(self, action: str):
        with open(self.webpage_path, 'r+', encoding='utf-8') as f:
            webpage_content = f.read()

        template = f"""
            HTML Code: {webpage_content}

            Using the HTML above for {self.current_url}, write a python playwright code function that takes a SINGLE argument of a playwright Page object and {action}. 
            Output ONLY the function with proper indents, nothing else. Do NOT use type annotations. Make sure that the playwright code is as specific and accurate as possible.

           ALSO, wait_for_navigation IS NOT A VALID PLAYWRIGHT FUNCTION

           Avoid using global page functions directly, instead using query_selector_all and then executing functions upon that \
           so for example instead of doing

           await page.click(".test:nth-child(1)")

           you would do

           elements = await page.locator("test").all()
           await elements[0].click()

           Remember to target <input> elements when trying to enter text! Remember to read the HTML itself and focus on it. Remember, you don't need to click on
           input elements to fill them, you can directly fill(). Be sure to use the HTML itself to generate the code, so that the generated playwright python code will work.

           Don't use networkidle as a load state to wait for, instead use domcontentloaded

            An example output (for formatting, etc) is 
            ```python\nasync def search_test(page):\n    await page.fill(\"#APjFqb\", \"cows\")\n    await page.click(\"input[name='btnK']\")\n```
        """

        response = self.model.generate_content(template)
        response = response.text
        response = self._remove_code_markers(response)

        function_path = generate_random_string()

        with open(f'{self.function_root}{function_path}.py', 'w+') as f:
            print(response)
            f.write(response)

        return function_path
    
# Try to avoid using global functions, such as instead of doing page.click('.x'), instead do 
#            elems = await page.query_selector_all('.x')
#            await elems[0].click()
#            so that you avoid errors when there are more than possible elements by a selector.    
