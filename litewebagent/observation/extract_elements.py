from playwright.sync_api import sync_playwright
import logging
import os
import time
import json
# from observation import _pre_extract

# Constants
# BID_ATTR = "data-bid"
# VIS_ATTR = "data-vis"
# SOM_ATTR = "data-som"
from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR

logger = logging.getLogger(__name__)

class MarkingError(Exception):
    pass

# def read_js_file(filepath):
#     with open(filepath, 'r', encoding='utf-8') as file:
#         return file.read()
#
# def mark_frames_recursive(frame, frame_bid: str, js_code: str):
#     assert frame_bid == "" or (frame_bid.islower() and frame_bid.isalpha())
#
#     warning_msgs = frame.evaluate(js_code, [frame_bid, BID_ATTR])
#     for msg in warning_msgs:
#         logger.warning(msg)
#
#     for child_frame in frame.child_frames:
#         if child_frame.is_detached():
#             continue
#         child_frame_elem = child_frame.frame_element()
#         if not child_frame_elem.content_frame() == child_frame:
#             logger.warning(f"Skipping frame '{child_frame.name}' for marking, seems problematic.")
#             continue
#         sandbox_attr = child_frame_elem.get_attribute("sandbox")
#         if sandbox_attr is not None and "allow-scripts" not in sandbox_attr.split():
#             continue
#         child_frame_bid = child_frame_elem.get_attribute(BID_ATTR)
#         if child_frame_bid is None:
#             raise MarkingError("Cannot mark a child frame without a bid.")
#         mark_frames_recursive(child_frame, frame_bid=child_frame_bid, js_code=js_code)
#
# def _pre_extract(page):
#     js_frame_mark_elements = read_js_file(
#         os.path.join(os.path.dirname(__file__), 'javascript', 'frame_mark_elements.js'))
#     mark_frames_recursive(page.main_frame, frame_bid="", js_code=js_frame_mark_elements)

def extract_interactive_elements(page):
    # _pre_extract(page)

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

        function getRandomColor() {
            var letters = "0123456789ABCDEF";
            var color = "#";
            for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
            }
            return color;
        }

        var bodyRect = document.body.getBoundingClientRect();
        var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

        var items = Array.prototype.slice
            .call(document.querySelectorAll("*"))
            .map(function (element) {
                var textualContent = element.textContent.trim().replace(/\\s{2,}/g, " ");
                var elementType = element.tagName.toLowerCase();
                var ariaLabel = element.getAttribute("aria-label") || "";
                var bid = element.getAttribute(browsergymIdAttribute) || "";

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
                    include:
                        element.tagName === "INPUT" ||
                        element.tagName === "TEXTAREA" ||
                        element.tagName === "SELECT" ||
                        element.tagName === "BUTTON" ||
                        element.tagName === "A" ||
                        element.onclick != null ||
                        window.getComputedStyle(element).cursor == "pointer" ||
                        element.tagName === "IFRAME" ||
                        element.tagName === "VIDEO",
                    area,
                    rects,
                    text: textualContent,
                    type: elementType,
                    ariaLabel: ariaLabel,
                    bid: bid
                };
            })
            .filter((item) => item.include && item.area >= 20);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x.element !== y.element && x.element.contains(y.element))
        );

        return items;
    }
    """

    return page.evaluate(js_code, BID_ATTR)

def highlight_elements(page, elements):
    js_code = """
    (elements) => {
        const labels = [];
        function unmarkPage() {
            for (const label of labels) {
                document.body.removeChild(label);
            }
            labels.length = 0;
        }

        unmarkPage();

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
                labels.push(newElement);
            });
        });
    }
    """
    page.evaluate(js_code, elements)

# def main():
#     with sync_playwright() as p:
#         browser = p.chromium.launch(headless=False)
#         page = browser.new_page()
#         page.goto('https://www.airbnb.com')
#         _pre_extract(page)
#
#         interactive_elements = extract_interactive_elements(page)
#         highlight_elements(page, interactive_elements)
#
#         # print(json.dumps(interactive_elements, indent=2))
#
#         time.sleep(30)  # Wait for 30 seconds
#
#         browser.close()
#
# if __name__ == "__main__":
#     main()


