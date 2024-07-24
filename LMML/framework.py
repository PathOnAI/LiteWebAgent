from bs4 import BeautifulSoup, NavigableString
import re

def extract_elements(html_string):
    soup = BeautifulSoup(html_string, 'html.parser')
    
    def is_empty(element):
        return not bool(element.get_text(strip=True)) and not element.find_all(['img', 'input', 'button', 'a', 'select', 'textarea'])

    def traverse(element):
        if isinstance(element, NavigableString):
            return ''

        is_interactable = element.name in ['a', 'button', 'input', 'select', 'textarea']
        
        if not is_empty(element) or is_interactable:
            output = str(element)
        else:
            output = ''.join(traverse(child) for child in element.children)

        return output

    return traverse(soup)