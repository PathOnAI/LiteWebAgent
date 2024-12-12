# copied and modified from https://github.com/ServiceNow/BrowserGym

import logging
import playwright.async_api
import pkgutil
from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR
from .constants import BROWSERGYM_SETOFMARKS_ATTRIBUTE as SOM_ATTR
from .constants import BROWSERGYM_VISIBILITY_ATTRIBUTE as VIS_ATTR
import os
import base64
import io
import logging
import playwright.async_api
import PIL.Image
import pkgutil
import re
import base64
import asyncio

MARK_FRAMES_MAX_TRIES = 3

logger = logging.getLogger(__name__)

from .extract_elements import extract_interactive_elements, highlight_elements

class MarkingError(Exception):
    pass

async def _pre_extract(page: playwright.async_api.Page):
    """
    pre-extraction routine, marks dom elements (set bid and dynamic attributes like value and checked)
    """
    js_frame_mark_elements = pkgutil.get_data(__name__, "javascript/frame_mark_elements.js").decode(
        "utf-8"
    )

    async def mark_frames_recursive(frame, frame_bid: str):
        assert frame_bid == "" or (frame_bid.islower() and frame_bid.isalpha())

        warning_msgs = await frame.evaluate(
            js_frame_mark_elements,
            [frame_bid, BID_ATTR],
        )
        for msg in warning_msgs:
            logger.warning(msg)

        for child_frame in frame.child_frames:
            if child_frame.is_detached():
                continue
            child_frame_elem = await child_frame.frame_element()
            if not await child_frame_elem.content_frame() == child_frame:
                logger.warning(
                    f"Skipping frame '{child_frame.name}' for marking, seems problematic."
                )
                continue
            sandbox_attr = await child_frame_elem.get_attribute("sandbox")
            if sandbox_attr is not None and "allow-scripts" not in sandbox_attr.split():
                continue
            child_frame_bid = await child_frame_elem.get_attribute(BID_ATTR)
            if child_frame_bid is None:
                logger.info("Cannot mark a child frame without a bid.")
            else:
                await mark_frames_recursive(child_frame, frame_bid=child_frame_bid)

    await mark_frames_recursive(page.main_frame, frame_bid="")

import time
async def extract_page_info(page, log_folder):
    page_info = {}
    await _pre_extract(page)
    await asyncio.sleep(3)
    screenshot_bytes = await page.screenshot()

    page_info['screenshot'] = screenshot_bytes
    page_info['dom'] = await extract_dom_snapshot(page)
    page_info['axtree'] = await extract_merged_axtree(page)
    page_info['focused_element'] = await extract_focused_element_bid(page)
    page_info['extra_properties'] = extract_dom_extra_properties(page_info.get('dom'))
    page_info['interactive_elements'] = await extract_interactive_elements(page)

    # fix extract_interactive_elements
    # highlight_elements
    # remove_highlights
    # flatten_interactive_elements_to_str
    # page are all async page
    await highlight_elements(page, page_info['interactive_elements'])
    await _post_extract(page)
    return page_info

async def _post_extract(page: playwright.async_api.Page):
    js_frame_unmark_elements = pkgutil.get_data(
        __name__, "javascript/frame_unmark_elements.js"
    ).decode("utf-8")

    for frame in page.frames:
        if not frame == page.main_frame:
            frame_element = await frame.frame_element()
            if not await frame_element.content_frame() == frame:
                logger.warning(f"Skipping frame '{frame.name}' for unmarking, seems problematic.")
                continue
            sandbox_attr = await frame_element.get_attribute("sandbox")
            if sandbox_attr is not None and "allow-scripts" not in sandbox_attr.split():
                continue

        try:
            await frame.evaluate(js_frame_unmark_elements)
        except playwright.async_api.Error as e:
            if "Frame was detached" in str(e):
                pass
            else:
                raise e

from PIL import Image
import base64
import io

async def extract_screenshot(page):
    """
    Extracts the screenshot image of a Playwright page using Chrome DevTools Protocol.
    """
    cdp = await page.context.new_cdp_session(page)
    cdp_answer = await cdp.send(
        "Page.captureScreenshot",
        {
            "format": "png",
        },
    )
    await cdp.detach()

    png_base64 = cdp_answer["data"]
    png_bytes = base64.b64decode(png_base64)
    with io.BytesIO(png_bytes) as f:
        img = Image.open(f)
        img = img.convert(mode="RGB")
        width, height = img.size
        pixels = list(img.getdata())
        img_list = [pixels[i * width:(i + 1) * width] for i in range(height)]

    return img_list

__BID_EXPR = r"([a-z0-9]+)"
__FLOAT_EXPR = r"([+-]?(?:[0-9]*[.])?[0-9]+)"
__BOOL_EXPR = r"([01])"
__DATA_REGEXP = re.compile(__BID_EXPR + r"_" + r"(.*)")

def extract_data_items_from_aria(string):
    """
    Utility function to extract temporary data stored in the "aria-roledescription" attribute of a node
    """
    match = __DATA_REGEXP.fullmatch(string)
    if not match:
        logger.warning(
            f'Data items could not be extracted from "aria-roledescription" attribute: {string}'
        )
        return [], string

    groups = match.groups()
    data_items = groups[:-1]
    original_aria = groups[-1]
    return data_items, original_aria

async def extract_dom_snapshot(
    page: playwright.async_api.Page,
    computed_styles=[],
    include_dom_rects: bool = True,
    include_paint_order: bool = True,
    temp_data_cleanup: bool = True,
):
    """
    Extracts the DOM snapshot of a Playwright page using Chrome DevTools Protocol.
    """
    cdp = await page.context.new_cdp_session(page)
    dom_snapshot = await cdp.send(
        "DOMSnapshot.captureSnapshot",
        {
            "computedStyles": computed_styles,
            "includeDOMRects": include_dom_rects,
            "includePaintOrder": include_paint_order,
        },
    )
    await cdp.detach()

    if temp_data_cleanup:
        try:
            target_attr_name_id = dom_snapshot["strings"].index("aria-roledescription")
        except ValueError:
            target_attr_name_id = -1
        if target_attr_name_id > -1:
            processed_string_ids = set()
            for document in dom_snapshot["documents"]:
                for node_attributes in document["nodes"]["attributes"]:
                    i = 0
                    for i in range(0, len(node_attributes), 2):
                        attr_name_id = node_attributes[i]
                        attr_value_id = node_attributes[i + 1]
                        if attr_name_id == target_attr_name_id:
                            attr_value = dom_snapshot["strings"][attr_value_id]
                            if attr_value_id not in processed_string_ids:
                                _, new_attr_value = extract_data_items_from_aria(attr_value)
                                dom_snapshot["strings"][attr_value_id] = new_attr_value
                                processed_string_ids.add(attr_value_id)
                                attr_value = new_attr_value
                            if attr_value == "":
                                del node_attributes[i : i + 2]
                            break

    return dom_snapshot

def extract_dom_extra_properties(dom_snapshot):
    def to_string(idx):
        if idx == -1:
            return None
        else:
            return dom_snapshot["strings"][idx]

    try:
        bid_string_id = dom_snapshot["strings"].index(BID_ATTR)
    except ValueError:
        bid_string_id = -1
    try:
        vis_string_id = dom_snapshot["strings"].index(VIS_ATTR)
    except ValueError:
        vis_string_id = -1
    try:
        som_string_id = dom_snapshot["strings"].index(SOM_ATTR)
    except ValueError:
        som_string_id = -1

    doc_properties = {
        0: {
            "parent": None,
        }
    }

    docs_to_process = [0]
    while docs_to_process:
        doc = docs_to_process.pop(-1)

        children = dom_snapshot["documents"][doc]["nodes"]["contentDocumentIndex"]
        for node, child_doc in zip(children["index"], children["value"]):
            doc_properties[child_doc] = {
                "parent": {
                    "doc": doc,
                    "node": node,
                }
            }
            docs_to_process.append(child_doc)

        parent = doc_properties[doc]["parent"]
        if parent:
            parent_doc = parent["doc"]
            parent_node = parent["node"]
            try:
                node_layout_idx = dom_snapshot["documents"][parent_doc]["layout"][
                    "nodeIndex"
                ].index(parent_node)
            except ValueError:
                node_layout_idx = -1
            if node_layout_idx >= 0:
                node_bounds = dom_snapshot["documents"][parent_doc]["layout"]["bounds"][
                    node_layout_idx
                ]
                parent_node_abs_x = doc_properties[parent_doc]["abs_pos"]["x"] + node_bounds[0]
                parent_node_abs_y = doc_properties[parent_doc]["abs_pos"]["y"] + node_bounds[1]
            else:
                parent_node_abs_x = 0
                parent_node_abs_y = 0
        else:
            parent_node_abs_x = 0
            parent_node_abs_y = 0

        doc_properties[doc]["abs_pos"] = {
            "x": parent_node_abs_x - dom_snapshot["documents"][doc]["scrollOffsetX"],
            "y": parent_node_abs_y - dom_snapshot["documents"][doc]["scrollOffsetY"],
        }

        document = dom_snapshot["documents"][doc]
        doc_properties[doc]["nodes"] = [
            {
                "bid": None,
                "visibility": None,
                "bbox": None,
                "clickable": False,
                "set_of_marks": None,
            }
            for _ in enumerate(document["nodes"]["parentIndex"])
        ]

        for node_idx in document["nodes"]["isClickable"]["index"]:
            doc_properties[doc]["nodes"][node_idx]["clickable"] = True

        for node_idx, node_attrs in enumerate(document["nodes"]["attributes"]):
            i = 0
            for i in range(0, len(node_attrs), 2):
                name_string_id = node_attrs[i]
                value_string_id = node_attrs[i + 1]
                if name_string_id == bid_string_id:
                    doc_properties[doc]["nodes"][node_idx]["bid"] = to_string(value_string_id)
                if name_string_id == vis_string_id:
                    doc_properties[doc]["nodes"][node_idx]["visibility"] = float(
                        to_string(value_string_id)
                    )
                if name_string_id == som_string_id:
                    doc_properties[doc]["nodes"][node_idx]["set_of_marks"] = (
                        to_string(value_string_id) == "1"
                    )

        for node_idx, bounds, client_rect in zip(
            document["layout"]["nodeIndex"],
            document["layout"]["bounds"],
            document["layout"]["clientRects"],
        ):
            if not client_rect:
                doc_properties[doc]["nodes"][node_idx]["bbox"] = None
            else:
                doc_properties[doc]["nodes"][node_idx]["bbox"] = bounds.copy()
                doc_properties[doc]["nodes"][node_idx]["bbox"][0] += doc_properties[doc]["abs_pos"][
                    "x"
                ]
                doc_properties[doc]["nodes"][node_idx]["bbox"][1] += doc_properties[doc]["abs_pos"][
                    "y"
                ]

    extra_properties = {}
    for doc in doc_properties.keys():
        for node in doc_properties[doc]["nodes"]:
            bid = node["bid"]
            if bid:
                if bid in extra_properties:
                    logger.warning(f"duplicate {BID_ATTR}={repr(bid)} attribute detected")
                extra_properties[bid] = {
                    extra_prop: node[extra_prop]
                    for extra_prop in ("visibility", "bbox", "clickable", "set_of_marks")
                }

    return extra_properties

async def extract_all_frame_axtrees(page: playwright.async_api.Page):
    """
    Extracts the AXTree of all frames (main document and iframes) of a Playwright page using Chrome DevTools Protocol.
    """
    cdp = await page.context.new_cdp_session(page)

    frame_tree = await cdp.send(
        "Page.getFrameTree",
        {},
    )

    frame_ids = []
    root_frame = frame_tree["frameTree"]
    frames_to_process = [root_frame]
    while frames_to_process:
        frame = frames_to_process.pop()
        frames_to_process.extend(frame.get("childFrames", []))
        frame_id = frame["frame"]["id"]
        frame_ids.append(frame_id)

    frame_axtrees = {
        frame_id: await cdp.send(
            "Accessibility.getFullAXTree",
            {"frameId": frame_id},
        )
        for frame_id in frame_ids
    }

    await cdp.detach()

    for ax_tree in frame_axtrees.values():
        for node in ax_tree["nodes"]:
            if "properties" in node:
                for i, prop in enumerate(node["properties"]):
                    if prop["name"] == "roledescription":
                        data_items, new_value = extract_data_items_from_aria(prop["value"]["value"])
                        prop["value"]["value"] = new_value
                        if new_value == "":
                            del node["properties"][i]
                        if data_items:
                            (browsergym_id,) = data_items
                            node["properties"].append(
                                {
                                    "name": "browsergym_id",
                                    "value": {
                                        "type": "string",
                                        "value": browsergym_id,
                                    },
                                }
                            )
    return frame_axtrees

async def extract_merged_axtree(page: playwright.async_api.Page):
    """
    Extracts the merged AXTree of a Playwright page (main document and iframes AXTrees merged) using Chrome DevTools Protocol.
    """
    frame_axtrees = await extract_all_frame_axtrees(page)

    cdp = await page.context.new_cdp_session(page)

    merged_axtree = {"nodes": []}
    for ax_tree in frame_axtrees.values():
        merged_axtree["nodes"].extend(ax_tree["nodes"])
        for node in ax_tree["nodes"]:
            if node["role"]["value"] == "Iframe":
                frame_id = (await cdp.send(
                    "DOM.describeNode", {"backendNodeId": node["backendDOMNodeId"]}
                ))["node"]["frameId"]
                if frame_id in frame_axtrees:
                    frame_root_node = frame_axtrees[frame_id]["nodes"][0]
                    assert frame_root_node["frameId"] == frame_id
                    node["childIds"].append(frame_root_node["nodeId"])
                else:
                    logger.warning(f"Extracted AXTree does not contain frameId '{frame_id}'")

    await cdp.detach()

    return merged_axtree

async def extract_focused_element_bid(page: playwright.async_api.Page):
    extract_focused_element_with_bid_script = """\
() => {
    function getActiveElement(root) {
        const active_element = root.activeElement;

        if (!active_element) {
            return null;
        }

        if (active_element.shadowRoot) {
            return getActiveElement(active_element.shadowRoot);
        } else {
            return active_element;
        }
    }
    return getActiveElement(document);
}"""
    frame = page
    focused_bid = ""
    while frame:
        focused_element = await frame.evaluate_handle(
            extract_focused_element_with_bid_script, BID_ATTR
        )
        focused_element = focused_element.as_element()
        if focused_element:
            frame = await focused_element.content_frame()
            focused_bid = await focused_element.get_attribute(BID_ATTR)
        else:
            frame = None

    return focused_bid