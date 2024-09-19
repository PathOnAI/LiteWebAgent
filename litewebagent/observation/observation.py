# copied and modified from https://github.com/ServiceNow/BrowserGym
import base64
import io
import logging
import numpy as np
import playwright.sync_api
import PIL.Image
import pkgutil
import re

from .constants import BROWSERGYM_ID_ATTRIBUTE as BID_ATTR
from .constants import BROWSERGYM_VISIBILITY_ATTRIBUTE as VIS_ATTR
from .constants import BROWSERGYM_SETOFMARKS_ATTRIBUTE as SOM_ATTR

MARK_FRAMES_MAX_TRIES = 3


logger = logging.getLogger(__name__)
from browsergym.core.observation import (
    _post_extract,
    extract_all_frame_axtrees,
    extract_dom_snapshot,
    extract_merged_axtree,
    extract_screenshot,
    extract_focused_element_bid,
    extract_dom_extra_properties,
    extract_data_items_from_aria,
)

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





