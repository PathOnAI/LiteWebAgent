from playwright.async_api import Page

import importlib
import inspect

import random



class ExecuteAgent:
    def __init__(self, page: Page):
        self.module = None
        self.function = None
        self.page = page

    def _is_async_function(self):
        try:
            return inspect.iscoroutinefunction(self.function)
        except:
            return None

    def load(self, name: str):
        self.module = importlib.import_module(f'cache.{name}')
        self.function = next(obj for name, obj in vars(self.module).items() if inspect.isfunction(obj))

        return self

    async def call(self): 
        # t = f'{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}/cache/cache.py'
        # with open(t, 'r+') as f:
        #     webpage_content = f.read()
        #     print(webpage_content)

        if self._is_async_function():
            await self.function(self.page)
            print('function called')
        else:
            self.function(self.page)



