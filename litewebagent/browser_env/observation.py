# copied and modified from https://github.com/ServiceNow/BrowserGym

import logging
import playwright.sync_api
import pkgutil
from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR
import os

MARK_FRAMES_MAX_TRIES = 3

logger = logging.getLogger(__name__)
from browsergym.core.observation import (
    _post_extract,
    extract_dom_snapshot,
    extract_merged_axtree,
    extract_focused_element_bid,
    extract_dom_extra_properties,
)
from litewebagent.browser_env.extract_elements import extract_interactive_elements, highlight_elements


class MarkingError(Exception):
    pass


def _pre_extract(page: playwright.sync_api.Page):
    """
    pre-extraction routine, marks dom elements (set bid and dynamic attributes like value and checked)
    """
    js_frame_mark_elements = pkgutil.get_data(__name__, "javascript/frame_mark_elements.js").decode(
        "utf-8"
    )

    # we can't run this loop in JS due to Same-Origin Policy
    # (can't access the content of an iframe from a another one)
    def mark_frames_recursive(frame, frame_bid: str):
        assert frame_bid == "" or (frame_bid.islower() and frame_bid.isalpha())

        # mark all DOM elements in the frame (it will use the parent frame element's bid as a prefix)
        warning_msgs = frame.evaluate(
            js_frame_mark_elements,
            [frame_bid, BID_ATTR],
        )
        # print warning messages if any
        for msg in warning_msgs:
            logger.warning(msg)

        # recursively mark all descendant frames
        for child_frame in frame.child_frames:
            # deal with detached frames
            if child_frame.is_detached():
                continue
            # deal with weird frames (pdf viewer in <embed>)
            child_frame_elem = child_frame.frame_element()
            if not child_frame_elem.content_frame() == child_frame:
                logger.warning(
                    f"Skipping frame '{child_frame.name}' for marking, seems problematic."
                )
                continue
            # deal with sandboxed frames with blocked script execution
            sandbox_attr = child_frame_elem.get_attribute("sandbox")
            if sandbox_attr is not None and "allow-scripts" not in sandbox_attr.split():
                continue
            child_frame_bid = child_frame_elem.get_attribute(BID_ATTR)
            if child_frame_bid is None:
                # raise MarkingError("Cannot mark a child frame without a bid.")
                # here's a temp fix, TODO: https://github.com/PathOnAI/LiteWebAgent/issues/32
                logger.info("Cannot mark a child frame without a bid.")
            else:
                mark_frames_recursive(child_frame, frame_bid=child_frame_bid)

    # mark all frames recursively
    mark_frames_recursive(page.main_frame, frame_bid="")


def extract_page_info(page, log_folder):
    page_info = {}
    _pre_extract(page)
    screenshot_path = os.path.join(log_folder, 'screenshots', 'screenshot_pre.png')
    page.screenshot(path=screenshot_path)
    page_info['screenshot'] = screenshot_path
    page_info['dom'] = extract_dom_snapshot(page)
    page_info['axtree'] = extract_merged_axtree(page)
    page_info['focused_element'] = extract_focused_element_bid(page)
    page_info['extra_properties'] = extract_dom_extra_properties(page_info.get('dom'))
    page_info['interactive_elements'] = extract_interactive_elements(page)
    highlight_elements(page, page_info['interactive_elements'])
    _post_extract(page)
    return page_info
