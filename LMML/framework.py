from bs4 import BeautifulSoup, Tag, NavigableString, Comment, Doctype
from typing import Union
from playwright.async_api import Page, async_playwright
import asyncio

# Define the type for a BeautifulSoup node
Node = Union[BeautifulSoup, Tag, NavigableString, Comment, Doctype]

class LMML:
    def __init__(self):
        self.page: Page | None = None
        self.content: BeautifulSoup | None = None

    async def recompile(self, page: Page, format=False):
        self.page = page
        content = await self.page.content()
        self.content = BeautifulSoup(content, 'lxml')

        for element in self.content(text=lambda text: isinstance(text, Comment)):
            element.extract()

        self.traverse(self.content)

        if format:
            return self.content.prettify()
        else:
            return self.content

    def traverse(self, node: Node):
        if isinstance(node, Tag):
            tags_to_remove = ['meta', 'script', 'style', 'link']
            interactive_elements = ['a', 'button', 'input', 'select', 'textarea', 'form']
            
            if node.name.lower() in tags_to_remove:
                node.decompose()
                return
            
            children = list(node.children)
            
            for child in children:
                self.traverse(child)
            
            if node.name.lower() in interactive_elements:
                return
            
            if node.parent is not None:
                direct_text = ''.join([str(t).strip() for t in node.contents if isinstance(t, NavigableString) and not isinstance(t, Comment)]).strip()
                
                if direct_text == '':
                    node.unwrap()

async def main():
    f = LMML()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        await page.goto('https://amazon.com')

        f_ = await f.recompile(page, format=True)
        with open('data3.html', 'w+', encoding="utf-8") as f:
            f.write(f_)


if __name__ == '__main__':
    asyncio.run(main())

    
    
    
    # print(extract_elements(test))