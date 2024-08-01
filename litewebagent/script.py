import playwright.sync_api
from typing import Literal


demo_mode='default'


def add_demo_mode_effects(
    page: playwright.sync_api.Page,
    elem: playwright.sync_api.ElementHandle,
    bid: str,
    demo_mode: Literal["off", "default", "all_blue", "only_visible_elements"],
    move_cursor: bool = True,
):
    if demo_mode == "off":
        return

    """Adds visual effects to the target element"""
    box = elem.bounding_box()
    # box = extract_bounds_cdp(page, bid)
    if box:
        center_x, center_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
        is_top_element = check_for_overlay(page, bid, elem, box)

        if demo_mode == "only_visible_elements":
            if not is_top_element:
                return
            else:
                color = "blue"

        elif demo_mode == "default":
            if is_top_element:
                color = "blue"
            else:
                color = "red"

        elif demo_mode == "all_blue":
            color = "blue"

        if move_cursor:
            smooth_move_visual_cursor_to(page, center_x, center_y)
        highlight_by_box(page, box, color=color)



def check_for_overlay(
    page: playwright.sync_api.Page, bid: str, element: playwright.sync_api.ElementHandle, box: dict
):
    if not element:
        return False

    visibility = element.get_attribute("browsergym_visibility_ratio")
    if visibility is not None:
        return float(visibility) >= 0.5

    """Checks if a given element is the topmost element at its center position by default.
    If check_corners is True, it checks if any of the corners is visible."""
    if box:
        # corners
        points_to_check = [
            (box["x"], box["y"]),
            (box["x"] + box["width"], box["y"]),
            (box["x"], box["y"] + box["height"]),
            (box["x"] + box["width"], box["y"] + box["height"]),
        ]

        for x, y in points_to_check:
            # Execute JavaScript to find the topmost element at the point.
            top_element = page.evaluate(
                f"""() => {{
                const el = document.elementFromPoint({x}, {y});
                return el ? el.outerHTML : '';
            }}"""
            )

            # Check if the topmost element is the element we're interested in.
            if top_element and bid in top_element:
                return True

    return False



def get_elem_by_bid(
    page: playwright.sync_api.Page, bid: str, scroll_into_view: bool = False
) -> playwright.sync_api.Locator:
    """
    Parse the given bid to sequentially locate every nested frame leading to the bid, then
    locate the bid element. Bids are expected to take the form "abb123", which means
    the element abb123 is located inside frame abb, which is located inside frame ab, which is
    located inside frame a, which is located inside the page's main frame.

    Args:
        bid: the browsergym id (playwright testid) of the page element.
        scroll_into_view: try to scroll element into view, unless it is completely visible.

    Returns:
        Playwright element.
        Bounding box of the element.
    """
    if not isinstance(bid, str):
        raise ValueError(f"expected a string, got {repr(bid)}")

    current_frame = page

    # dive into each nested frame, to the frame where the element is located
    i = 0
    while bid[i:] and not bid[i:].isnumeric():
        i += 1
        frame_bid = bid[:i]  # bid of the next frame to select
        frame_elem = current_frame.get_by_test_id(frame_bid)
        if not frame_elem.count():
            raise ValueError(f'Could not find element with bid "{bid}"')
        if scroll_into_view:
            frame_elem.scroll_into_view_if_needed(timeout=500)
        current_frame = frame_elem.frame_locator(":scope")

    # finally, we should have selected the frame where the target element is
    elem = current_frame.get_by_test_id(bid)
    if not elem.count():
        raise ValueError(f'Could not find element with bid "{bid}"')
    if scroll_into_view:
        elem.scroll_into_view_if_needed(timeout=500)
    return elem



def highlight_by_box(
    page: playwright.sync_api.Page, box: dict, color: Literal["blue", "red"] = "blue"
):
    """Highlights the target element based on its bounding box attributes."""

    assert color in ("blue", "red")

    if box:
        left, top, width, height = box["x"], box["y"], box["width"], box["height"]
        page.evaluate(
            f"""\
const overlay = document.createElement('div');
document.body.appendChild(overlay);
overlay.setAttribute('style', `
    all: initial;
    position: fixed;
    border: 2px solid transparent;  /* Start with transparent border */
    borderRadius: 10px;  /* Add rounded corners */
    boxShadow: 0 0 0px {color};  /* Initial boxShadow with 0px spread */
    left: {left - 2}px;  /* Adjust left position to accommodate initial shadow spread */
    top: {top - 2}px;  /* Adjust top position likewise */
    width: {width}px;
    height: {height}px;
    z-index: 2147483646; /* Maximum value - 1 */
    pointerEvents: none; /* Ensure the overlay does not interfere with user interaction */
`);

// Animate the boxShadow to create a "wave" effect
let spread = 0;  // Initial spread radius of the boxShadow
const waveInterval = setInterval(() => {{
    spread += 10;  // Increase the spread radius to simulate the wave moving outward
    overlay.style.boxShadow = `0 0 40px ${{spread}}px {color}`;  // Update boxShadow to new spread radius
    overlay.style.opacity = 1 - spread / 38;  // Gradually decrease opacity to fade out the wave
    if (spread >= 38) {{  // Assuming 76px ~ 2cm spread radius
        clearInterval(waveInterval);  // Stop the animation once the spread radius reaches 2cm
        document.body.removeChild(overlay);  // Remove the overlay from the document
    }}
}}, 200);  // Adjust the interval as needed to control the speed of the wave animation
"""
        )
        # Wait a bit to let users see the highlight
        page.wait_for_timeout(1000)  # Adjust delay as needed



def smooth_move_visual_cursor_to(
    page: playwright.sync_api.Page, x: float, y: float, speed: float = 400
):
    """
    Smoothly moves the visual cursor to a specific point, with constant
    movement speed.

    Args:
        x: target location X coordinate (in viewport pixels)
        y: target location Y coordinate (in viewport pixels)
        speed: cursor speed (in pixels per second)
    """
    movement_time = page.evaluate(
        """\
    ([targetX, targetY, speed]) => {

        // create cursor if needed
        if (!("browsergym_visual_cursor" in window)) {
            if (window.trustedTypes && window.trustedTypes.createPolicy) {
                window.trustedTypes.createPolicy('default', {
                    createHTML: (string, sink) => string
                });
            }
            let cursor = document.createElement('div');
            cursor.setAttribute('id', 'browsergym-visual-cursor');
            cursor.innerHTML = `
                <svg width="50px" height="50px" viewBox="213 106 713 706" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M213.333 106.667L426.667 853.333 512 512 853.333 426.667 213.333 106.667z" fill="blue"/>
                </svg>
`;
            cursor.setAttribute('style', `
                all: initial;
                position: fixed;
                opacity: 0.7; /* Slightly transparent */
                z-index: 2147483647; /* Maximum value */
                pointer-events: none; /* Ensures the SVG doesn't interfere with page interactions */
            `);

            // Calculate center position within the viewport
            const centerX = window.innerWidth / 2;
            const centerY = window.innerHeight / 2;

            cursor.style.left = `${centerX}px`;
            cursor.style.top = `${centerY}px`;

            // save cursor element
            window.browsergym_visual_cursor = cursor;
            window.browsergym_visual_cursor_n_owners = 0;
        }

        // recover cursor
        let cursor = window.browsergym_visual_cursor;

        // attach cursor to document
        document.body.appendChild(cursor);
        window.browsergym_visual_cursor_n_owners += 1;

        x = parseFloat(cursor.style.left);
        y = parseFloat(cursor.style.top);

        dx = targetX - x;
        dy = targetY - y;
        dist = Math.hypot(dx, dy);
        movement_time = (dist / speed) * 1000;  // seconds to milliseconds
        still_wait_time = 1000;

        // Adjust steps based on distance to keep movement speed consistent
        // 1 step per 10 pixels of distance, adjust as needed
        steps = Math.max(1, Math.trunc(dist / 10));

        step_dx = dx / steps;
        step_dy = dy / steps;
        step_dist = dist / steps;
        step_wait_time = Math.max(10, movement_time / steps);

        let step = 0;
        let time_still = 0;
        const cursorInterval = setInterval(() => {
            // move cursor
            if (step < steps) {
                x += step_dx;
                y += step_dy;
                cursor.style.left = `${x}px`;
                cursor.style.top = `${y}px`;
            }
            // still cursor (wait a bit)
            else if (time_still < still_wait_time) {
                time_still += step_wait_time;
            }
            // stop and detach cursor
            else {
                clearInterval(cursorInterval);
                window.browsergym_visual_cursor_n_owners -= 1;
                if (window.browsergym_visual_cursor_n_owners <= 0) {
                    document.body.removeChild(cursor);

                }
            }
            step += 1;
        }, step_wait_time);

        return movement_time;
    }""",
        [x, y, speed],
    )
    page.wait_for_timeout(movement_time)



def noop(wait_ms: float = 1000):
    """
    Do nothing, and optionally wait for the given time (in milliseconds).

    Examples:
        noop()
        noop(500)
    """
    page.wait_for_timeout(wait_ms)



def send_msg_to_user(text: str):
    """
    Sends a message to the user.

    Examples:
        send_msg_to_user("Based on the results of my search, the city was built in 1751.")
    """
    send_message_to_user(text)



def scroll(delta_x: float, delta_y: float):
    """
    Scroll horizontally and vertically. Amounts in pixels, positive for right or down scrolling, negative for left or up scrolling. Dispatches a wheel event.

    Examples:
        scroll(0, 200)
        scroll(-50.2, -100.5)
    """
    page.mouse.wheel(delta_x, delta_y)



def fill(bid: str, value: str):
    """
    Fill out a form field. It focuses the element and triggers an input event with the entered text.
    It works for <input>, <textarea> and [contenteditable] elements.

    Examples:
        fill('237', 'example value')
        fill('45', "multi-line\\nexample")
        fill('a12', "example with \\"quotes\\"")
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    if demo_mode != "off":
        elem.clear()
        delay = max(2000 / len(value), 10)
        elem.type(value, delay=delay)
    else:
        elem.fill(value, timeout=500)



def select_option(bid: str, options: str | list[str]):
    """
    Select one or multiple options in a <select> element. You can specify
    option value or label to select. Multiple options can be selected.

    Examples:
        select_option('a48', "blue")
        select_option('c48', ["red", "green", "blue"])
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    elem.select_option(options, timeout=500)



def click(
    bid: str,
    button: Literal["left", "middle", "right"] = "left",
    modifiers: list[Literal["Alt", "Control", "Meta", "Shift"]] = [],
):
    """
    Click an element.

    Examples:
        click('a51')
        click('b22', button="right")
        click('48', button="middle", modifiers=["Shift"])
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)
    elem.click(button=button, modifiers=modifiers, timeout=500)



def dblclick(
    bid: str,
    button: Literal["left", "middle", "right"] = "left",
    modifiers: list[Literal["Alt", "Control", "Meta", "Shift"]] = [],
):
    """
    Double click an element.

    Examples:
        dblclick('12')
        dblclick('ca42', button="right")
        dblclick('178', button="middle", modifiers=["Shift"])
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)
    elem.dblclick(button=button, modifiers=modifiers, timeout=500)



def hover(bid: str):
    """
    Hover over an element.

    Examples:
        hover('b8')
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    if demo_mode != "off":
        box = elem.bounding_box()
        if box:
            center_x, center_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            smooth_move_visual_cursor_to(page, center_x, center_y)
    elem.hover(timeout=500)



def press(bid: str, key_comb: str):
    """
    Focus the matching element and press a combination of keys. It accepts
    the logical key names that are emitted in the keyboardEvent.key property
    of the keyboard events: Backquote, Minus, Equal, Backslash, Backspace,
    Tab, Delete, Escape, ArrowDown, End, Enter, Home, Insert, PageDown, PageUp,
    ArrowRight, ArrowUp, F1 - F12, Digit0 - Digit9, KeyA - KeyZ, etc. You can
    alternatively specify a single character you'd like to produce such as "a"
    or "#". Following modification shortcuts are also supported: Shift, Control,
    Alt, Meta.

    Examples:
        press('88', 'Backspace')
        press('a26', 'Control+a')
        press('a61', 'Meta+Shift+t')
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    elem.press(key_comb, timeout=500)



def focus(bid: str):
    """
    Focus the matching element.

    Examples:
        focus('b455')
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    elem.focus(timeout=500)



def clear(bid: str):
    """
    Clear the input field.

    Examples:
        clear('996')
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    elem.clear(timeout=500)



def drag_and_drop(from_bid: str, to_bid: str):
    """
    Perform a drag & drop. Hover the element that will be dragged. Press
    left mouse button. Move mouse to the element that will receive the
    drop. Release left mouse button.

    Examples:
        drag_and_drop('56', '498')
    """
    from_elem = get_elem_by_bid(page, from_bid, demo_mode != "off")
    add_demo_mode_effects(page, from_elem, from_bid, demo_mode=demo_mode, move_cursor=True)
    from_elem.hover(timeout=500)
    page.mouse.down()

    to_elem = get_elem_by_bid(page, to_bid, demo_mode != "off")
    add_demo_mode_effects(page, to_elem, to_bid, demo_mode=demo_mode, move_cursor=True)
    to_elem.hover(timeout=500)
    page.mouse.up()



def upload_file(bid: str, file: str | list[str]):
    """
    Click an element and wait for a "filechooser" event, then select one
    or multiple input files for upload. Relative file paths are resolved
    relative to the current working directory. An empty list clears the
    selected files.

    Examples:
        upload_file("572", "my_receipt.pdf")
        upload_file("63", ["/home/bob/Documents/image.jpg", "/home/bob/Documents/file.zip"])
    """
    elem = get_elem_by_bid(page, bid, demo_mode != "off")
    add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)

    with page.expect_file_chooser() as fc_info:
        elem.click(timeout=500)

    file_chooser = fc_info.value
    file_chooser.set_files(file)



def go_back():
    """
    Navigate to the previous page in history.

    Examples:
        go_back()
    """
    page.go_back()



def go_forward():
    """
    Navigate to the next page in history.

    Examples:
        go_forward()
    """
    page.go_forward()



def goto(url: str):
    """
    Navigate to a url.

    Examples:
        goto('http://www.example.com')
    """
    page.goto(url)



def mouse_move(x: float, y: float):
    """
    Move the mouse to a location. Uses absolute client coordinates in pixels.
    Dispatches a mousemove event.

    Examples:
        mouse_move(65.2, 158.5)
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
    page.mouse.move(x, y)



def mouse_up(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location then release a mouse button. Dispatches
    mousemove and mouseup events.

    Examples:
        mouse_up(250, 120)
        mouse_up(47, 252, 'right')
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.move(x, y)
    page.mouse.up(button=button)



def mouse_down(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location then press and hold a mouse button. Dispatches
    mousemove and mousedown events.

    Examples:
        mouse_down(140.2, 580.1)
        mouse_down(458, 254.5, 'middle')
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.move(x, y)
    page.mouse.down(button=button)



def mouse_click(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location and click a mouse button. Dispatches mousemove,
    mousedown and mouseup events.

    Examples:
        mouse_click(887.2, 68)
        mouse_click(56, 712.56, 'right')
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.click(x, y, button=button)



def mouse_dblclick(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location and double click a mouse button. Dispatches
    mousemove, mousedown and mouseup events.

    Examples:
        mouse_dblclick(5, 236)
        mouse_dblclick(87.5, 354, 'right')
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.dblclick(x, y, button=button)



def mouse_drag_and_drop(from_x: float, from_y: float, to_x: float, to_y: float):
    """
    Drag and drop from a location to a location. Uses absolute client
    coordinates in pixels. Dispatches mousemove, mousedown and mouseup
    events.

    Examples:
        mouse_drag_and_drop(10.7, 325, 235.6, 24.54)
    """
    if demo_mode != "off":
        x, y = from_x, from_y
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.move(from_x, from_y)
    page.mouse.down()
    if demo_mode != "off":
        x, y = to_x, to_y
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    page.mouse.move(to_x, to_y)
    page.mouse.up()



def mouse_upload_file(x: float, y: float, file: str | list[str]):
    """
    Click a location and wait for a "filechooser" event, then select one
    or multiple input files for upload. Relative file paths are resolved
    relative to the current working directory. An empty list clears the
    selected files.

    Examples:
        mouse_upload_file(132.1, 547, "my_receipt.pdf")
        mouse_upload_file(328, 812, ["/home/bob/Documents/image.jpg", "/home/bob/Documents/file.zip"])
    """
    if demo_mode != "off":
        smooth_move_visual_cursor_to(page, x, y)
        highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})

    with page.expect_file_chooser() as fc_info:
        page.mouse.click(x, y)

    file_chooser = fc_info.value
    file_chooser.set_files(file)



def keyboard_down(key: str):
    """
    Press and holds a keyboard key. Dispatches a keydown event. Accepts the
    logical key names that are emitted in the keyboardEvent.key property of
    the keyboard events: Backquote, Minus, Equal, Backslash, Backspace, Tab,
    Delete, Escape, ArrowDown, End, Enter, Home, Insert, PageDown, PageUp,
    ArrowRight, ArrowUp, F1 - F12, Digit0 - Digit9, KeyA - KeyZ, etc. You can
    alternatively specify a single character such as "a" or "#".

    Examples:
        keyboard_up('Shift')
        keyboard_up('c')
    """
    page.keyboard.down(key)



def keyboard_up(key: str):
    """
    Release a keyboard key. Dispatches a keyup event. Accepts the logical
    key names that are emitted in the keyboardEvent.key property of the
    keyboard events: Backquote, Minus, Equal, Backslash, Backspace, Tab,
    Delete, Escape, ArrowDown, End, Enter, Home, Insert, PageDown, PageUp,
    ArrowRight, ArrowUp, F1 - F12, Digit0 - Digit9, KeyA - KeyZ, etc.
    You can alternatively specify a single character you'd like to produce
    such as "a" or "#".

    Examples:
        keyboard_up('Shift')
        keyboard_up('c')
    """
    page.keyboard.up(key)



def keyboard_press(key: str):
    """
    Press a combination of keys. Accepts the logical key names that are
    emitted in the keyboardEvent.key property of the keyboard events:
    Backquote, Minus, Equal, Backslash, Backspace, Tab, Delete, Escape,
    ArrowDown, End, Enter, Home, Insert, PageDown, PageUp, ArrowRight,
    ArrowUp, F1 - F12, Digit0 - Digit9, KeyA - KeyZ, etc. You can
    alternatively specify a single character you'd like to produce such
    as "a" or "#". Following modification shortcuts are also supported:
    Shift, Control, Alt, Meta.

    Examples:
        keyboard_press('Backspace')
        keyboard_press('Control+a')
        keyboard_press('Meta+Shift+t')
        page.keyboard.press("PageDown")
    """
    page.keyboard.press(key)



def keyboard_type(text: str):
    """
    Types a string of text through the keyboard. Sends a keydown, keypress/input,
    and keyup event for each character in the text. Modifier keys DO NOT affect
    keyboard_type. Holding down Shift will not type the text in upper case.

    Examples:
        keyboard_type('Hello world!')
    """
    if demo_mode:
        delay = max(2000 / len(text), 10)
    else:
        delay = None
    page.keyboard.type(text, delay=delay)



def keyboard_insert_text(text: str):
    """
    Insert a string of text in the currently focused element. Dispatches only input
    event, does not emit the keydown, keyup or keypress events. Modifier keys DO NOT
    affect keyboard_insert_text. Holding down Shift will not type the text in upper
    case.

    Examples:
        keyboard_insert_text('Hello world!')
    """
    page.keyboard.insert_text(text)



click('648')
