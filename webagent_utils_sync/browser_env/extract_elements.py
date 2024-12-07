import logging
from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR

logger = logging.getLogger(__name__)


class MarkingError(Exception):
    pass


def extract_interactive_elements(page):
    js_code = """
    (browsergymIdAttribute) => {
        const customCSS = `
            ::-webkit-scrollbar {
                width: 10px;
            }
            ::-webkit-scrollbar-track {
                background: #27272a;
            }
            ::-webkit-scrollbar-thumb {
                background: #888;
                border-radius: 0.375rem;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: #555;
            }
        `;

        const styleTag = document.createElement("style");
        styleTag.textContent = customCSS;
        document.head.append(styleTag);

        function generateSelector(element) {
            let selector = element.tagName.toLowerCase();
            if (element.id) {
                selector += `#${element.id}`;
            } else {
                if (typeof element.className === 'string' && element.className.trim()) {
                    selector += `.${element.className.trim().split(/\\s+/).join('.')}`;
                }
                let sibling = element;
                let nth = 1;
                while (sibling = sibling && sibling.previousElementSibling) {
                    if (sibling.tagName.toLowerCase() === selector.split('.')[0]) nth++;
                }
                if (nth > 1) {
                    selector += `:nth-of-type(${nth})`;
                }
            }
            return selector;
        }

        function isInteractive(element) {
            const interactiveTags = [
                'a', 'button', 'input', 'select', 'textarea', 'summary', 'video', 'audio',
                'iframe', 'embed', 'object', 'menu', 'label', 'fieldset', 'datalist', 'output',
                'details', 'dialog', 'option'
            ];
            const interactiveRoles = [
                'button', 'link', 'checkbox', 'radio', 'menuitem', 'menuitemcheckbox', 'menuitemradio',
                'option', 'listbox', 'textbox', 'combobox', 'slider', 'spinbutton', 'scrollbar',
                'tabpanel', 'treeitem', 'switch', 'searchbox', 'grid', 'gridcell', 'row',
                'rowgroup', 'rowheader', 'columnheader', 'tab', 'tooltip', 'application', 
                'dialog', 'alertdialog', 'progressbar'
            ];
            
            return interactiveTags.includes(element.tagName.toLowerCase()) ||
                   interactiveRoles.includes(element.getAttribute('role')) ||
                   element.onclick != null ||
                   element.onkeydown != null ||
                   element.onkeyup != null ||
                   element.onkeypress != null ||
                   element.onchange != null ||
                   element.onfocus != null ||
                   element.onblur != null ||
                   element.getAttribute('tabindex') !== null ||
                   element.getAttribute('contenteditable') === 'true';
        }

        var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

        var items = Array.prototype.slice
            .call(document.querySelectorAll("*"))
            .map(function (element) {
                var bid = element.getAttribute(browsergymIdAttribute) || "";

                // Only process elements with a non-empty browsergymIdAttribute AND that are interactive
                if (bid === "" || !isInteractive(element)) {
                    return null;
                }

                var textualContent = element.textContent.trim().replace(/\\s{2,}/g, " ");
                var elementType = element.tagName.toLowerCase();
                var ariaLabel = element.getAttribute("aria-label") || "";

                var rects = [...element.getClientRects()]
                    .filter((bb) => {
                        var center_x = bb.left + bb.width / 2;
                        var center_y = bb.top + bb.height / 2;
                        var elAtCenter = document.elementFromPoint(center_x, center_y);
                        return elAtCenter === element || element.contains(elAtCenter);
                    })
                    .map((bb) => {
                        const rect = {
                            left: Math.max(0, bb.left),
                            top: Math.max(0, bb.top),
                            right: Math.min(vw, bb.right),
                            bottom: Math.min(vh, bb.bottom),
                        };
                        return {
                            ...rect,
                            width: rect.right - rect.left,
                            height: rect.bottom - rect.top,
                        };
                    });

                var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);

                return {
                    include: true,
                    area: area,
                    rects: rects,
                    text: textualContent,
                    type: elementType,
                    ariaLabel: ariaLabel,
                    bid: bid,
                    tag: elementType,
                    id: element.id || null,
                    class: typeof element.className === 'string' ? element.className : null,
                    href: element.getAttribute("href") || null,
                    title: element.getAttribute("title") || null
                };
            })
            .filter((item) => item !== null && item.area >= 20);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x !== y && document.querySelector(`[id="${y.bid}"]`) && document.querySelector(`[id="${y.bid}"]`).contains(document.querySelector(`[id="${x.bid}"]`)))
        );

        return items;
    }
    """

    return page.evaluate(js_code, BID_ATTR)


def highlight_elements(page, elements, max_retries=3, retry_delay=1000):
    js_code = """
    (elements) => {
        if (!window.litewebagentLabels) {
            window.litewebagentLabels = [];
        }
        function unmarkPage() {
            for (const label of window.litewebagentLabels) {
                if (label && label.parentNode) {
                    label.parentNode.removeChild(label);
                }
            }
            window.litewebagentLabels.length = 0;
        }
        unmarkPage();
        let highlightedCount = 0;
        elements.forEach((item, index) => {
            item.rects.forEach((bbox) => {
                const newElement = document.createElement("div");
                const borderColor = `#${Math.floor(Math.random()*16777215).toString(16)}`;
                newElement.style.outline = `2px dashed ${borderColor}`;
                newElement.style.position = "fixed";
                newElement.style.left = `${bbox.left}px`;
                newElement.style.top = `${bbox.top}px`;
                newElement.style.width = `${bbox.width}px`;
                newElement.style.height = `${bbox.height}px`;
                newElement.style.pointerEvents = "none";
                newElement.style.boxSizing = "border-box";
                newElement.style.zIndex = 2147483647;
                const label = document.createElement("span");
                label.textContent = `${item.bid}`;
                label.style.position = "absolute";
                label.style.top = "-19px";
                label.style.left = "0px";
                label.style.background = borderColor;
                label.style.color = "white";
                label.style.padding = "2px 4px";
                label.style.fontSize = "12px";
                label.style.borderRadius = "2px";
                newElement.appendChild(label);
                document.body.appendChild(newElement);
                window.litewebagentLabels.push(newElement);
                highlightedCount++;
            });
        });
        return highlightedCount;
    }
    """

    for attempt in range(max_retries):
        highlighted_count = page.evaluate(js_code, elements)
        if highlighted_count == len(elements):
            logger.info(f"All {highlighted_count} elements highlighted successfully.")
            return

        logger.info(
            f"Attempt {attempt + 1}: Highlighted {highlighted_count}/{len(elements)} elements. Retrying in {retry_delay}ms...")
        page.wait_for_timeout(retry_delay)

    logger.info(f"Warning: Only {highlighted_count}/{len(elements)} elements were highlighted after {max_retries} attempts.")


def remove_highlights(page):
    js_code = """
    () => {
        if (window.litewebagentLabels) {
            for (const label of window.litewebagentLabels) {
                if (label && label.parentNode) {
                    label.parentNode.removeChild(label);
                }
            }
            window.litewebagentLabels.length = 0;
        }
    }
    """
    page.evaluate(js_code)


def flatten_interactive_elements_to_str(
        interactive_elements,
        indent_char="\t"
):
    """
    Formats a list of interactive elements into a string, including only text, type, and bid.
    Skips elements where the type is 'html'.

    :param interactive_elements: List of dictionaries containing interactive element data
    :param indent_char: Character used for indentation (default: tab)
    :return: Formatted string representation of interactive elements
    """

    def format_element(element):
        # Skip if element type is 'html'
        if element.get('type', '').lower() == 'html' or element.get('type', '').lower() == 'body':
            return None

        # Add bid if present
        bid = f"[{element['bid']}] " if 'bid' in element else ""

        # Basic element info
        element_type = element.get('type', 'Unknown')
        text = element.get('text', '').replace('\n', ' ')

        return f"{bid}{element_type} {repr(text)}"

    formatted_elements = [
        formatted_elem for elem in interactive_elements
        if elem.get('include', True)
        for formatted_elem in [format_element(elem)]
        if formatted_elem is not None
    ]
    return "\n".join(formatted_elements)
