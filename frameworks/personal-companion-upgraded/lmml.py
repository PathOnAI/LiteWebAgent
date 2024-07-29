from bs4 import BeautifulSoup, Tag, NavigableString, Comment, Doctype
from typing import Union
from playwright.async_api import Page, async_playwright
import asyncio

from copy import deepcopy

# Define the type for a BeautifulSoup node
Node = Union[BeautifulSoup, Tag, NavigableString, Comment, Doctype]


class LMML:
    def __init__(self):
        self.page: Page | None = None
        self.content: BeautifulSoup | None = None

    async def recompile(self, page: Page, format=False):
        self.page = page
        # content = await self.page.content()
        content = await self.page.evaluate('''() => {
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

        self.content = BeautifulSoup(content, 'lxml')

        content_copy = deepcopy(self.content)

        for element in self.content(text=lambda text: isinstance(text, Comment)):
            element.extract()

        self.traverse(self.content)

        if format:
            return self.content.prettify(), content_copy.prettify()
        else:
            return self.content, content_copy

    def traverse(self, node: Node):
        if isinstance(node, Tag):
            tags_to_remove = ['meta', 'script', 'style', 'link']
            interactive_elements = ['a', 'button',
                                    'input', 'select', 'textarea', 'form']

            if node.name.lower() in tags_to_remove:
                node.decompose()
                return

            children = list(node.children)

            for child in children:
                self.traverse(child)

            if node.name.lower() in interactive_elements:
                return

            if node.parent is not None:
                direct_text = ''.join([str(t).strip() for t in node.contents if isinstance(
                    t, NavigableString) and not isinstance(t, Comment)]).strip()

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
