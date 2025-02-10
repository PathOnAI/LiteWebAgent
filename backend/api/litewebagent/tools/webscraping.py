from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import random
from .registry import ToolRegistry, Tool

def webscraping(task_description, features=None, branching_factor=None, playwright_manager=None, log_folder='log', s3_path = None, elements_filter=None):
    max_retries = 3
    page = playwright_manager.get_page()

    for attempt in range(max_retries):
        try:
            # Wait for potential Cloudflare challenge to be solved
            page.wait_for_load_state('networkidle')

            # Check if we're still on a Cloudflare page
            title = page.title()
            if 'cloudflare' in title.lower():
                print(f"Cloudflare detected, waiting... (Attempt {attempt + 1})")
                time.sleep(5)  # Wait for 5 seconds before retrying
                continue

            # Get the current URL
            current_url = page.url

            page_content = page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Remove unwanted elements
            for element in soup.select('aside, header, nav, footer'):
                element.decompose()

            # Extract content
            content = {
                'url': current_url,
                'title': page.title(),
                'main_content': get_main_content(soup),
                'paragraphs': get_paragraphs(soup),
                'headings': get_headings(soup),
                'meta_data': get_meta_data(soup),
                'internal_links': get_internal_links(soup, current_url),
                'formatted_content': get_formatted_content(soup)
            }

            return content

        except Exception as e:
            print(f"Error occurred: {e}")
            if attempt == max_retries - 1:
                raise
            time.sleep(random.uniform(1, 3))


def get_main_content(soup):
    main_content = soup.find(id='main')
    return main_content.text if main_content else "Main content not found"


def get_paragraphs(soup):
    return [p.text for p in soup.find_all('p')]


def get_headings(soup):
    return [h.text for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])]


def get_meta_data(soup):
    meta_data = {}
    for meta_tag in soup.find_all('meta'):
        name = meta_tag.get('name') or meta_tag.get('property')
        content = meta_tag.get('content')
        if name and content:
            meta_data[name] = content
    return meta_data


def get_internal_links(soup, url):
    internal_links = []
    base_url = urlparse(url).scheme + "://" + urlparse(url).hostname

    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.startswith('/'):
            full_url = urljoin(base_url, href)
            internal_links.append(full_url)
        elif href.startswith(base_url):
            internal_links.append(href)

    return internal_links


def get_formatted_content(soup):
    formatted_article = []
    unique_text = set()
    tag_names = set(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'ul', 'ol'])
    ignore_classes = {'ch2-container', 'ch2-theme-bar', 'ch2-style-light',
                      'ch2-dialog', 'ch2-dialog-bottom', 'ch2-visible',
                      'ch2-settings', 'ch2-settings-scan'}

    for tag in soup.find_all(True):
        if tag.name in tag_names:
            if not any(cls in ignore_classes for cls in tag.get('class', [])) and \
                    not any(cls in ignore_classes for parent in tag.parents for cls in parent.get('class', [])):
                if not any(child.name in tag_names for child in tag.children):
                    text = tag.get_text().strip()
                    lower_text = text.lower()
                    if text and lower_text not in unique_text:
                        unique_text.add(lower_text)
                        formatted_article.append(f"{text} \n")

    return ''.join(formatted_article)


def register_webscraping_tool():
    ToolRegistry.register(Tool(
        name="webscraping",
        func=webscraping,
        description="Scrape content from the current web page",
        parameters={
            "task_description": {
                "type": "string",
                "description": "The description of the webscraping task"
            }
        }
    ))