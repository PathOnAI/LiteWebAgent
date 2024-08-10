import html2text
import argparse
import os

def html_file_to_markdown(file_path):
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' not found."

        # Read the HTML file
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()

        # Convert HTML to Markdown
        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = False
        markdown_content = h.handle(html_content)

        return markdown_content

    except Exception as e:
        return f"Error converting HTML to Markdown: {e}"

def main():
    parser = argparse.ArgumentParser(description="Convert local HTML file to Markdown")
    parser.add_argument("file", help="Path to the local HTML file")
    parser.add_argument("-o", "--output", help="Output file name (optional)")
    args = parser.parse_args()

    markdown_content = html_file_to_markdown(args.file)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"Markdown content saved to {args.output}")
    else:
        print(markdown_content)

if __name__ == "__main__":
    main()