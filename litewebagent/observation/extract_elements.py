from playwright.sync_api import sync_playwright
import logging
import os
import time
import json

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

        var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
        var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);

        var items = Array.prototype.slice
            .call(document.querySelectorAll("*"))
            .map(function (element) {
                var textualContent = element.textContent.trim().replace(/\\s{2,}/g, " ");
                var elementType = element.tagName.toLowerCase();
                var ariaLabel = element.getAttribute("aria-label") || "";
                var bid = element.getAttribute(browsergymIdAttribute) || generateSelector(element);

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
            .filter((item) => item.include && item.area >= 20);

        // Only keep inner clickable items
        items = items.filter(
            (x) => !items.some((y) => x !== y && document.querySelector(`[id="${y.bid}"]`) && document.querySelector(`[id="${y.bid}"]`).contains(document.querySelector(`[id="${x.bid}"]`)))
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


