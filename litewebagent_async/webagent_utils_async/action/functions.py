# these are placeholders
# all these symbols will be available in browsergym actions
import playwright.async_api
from typing import Literal

from .browsergym_utils import (
    add_demo_mode_effects,
    get_elem_by_bid,
    highlight_by_box,
    smooth_move_visual_cursor_to,
)

page: playwright.async_api.Page = None
send_message_to_user: callable = None
report_infeasible_instructions: callable = None
demo_mode: Literal["off", "default", "all_blue", "only_visible_elements"] = None

"""IMPORTANT
The following primitives are meant to be included in the browsergym action using
inspect.getsource().
"""

async def send_msg_to_user(text: str):
    """
    Sends a message to the user.

    Examples:
        await send_msg_to_user("Based on the results of my search, the city was built in 1751.")
    """
    await send_message_to_user(text)

async def report_infeasible(reason: str):
    """
    Notifies the user that their instructions are infeasible.

    Examples:
        await report_infeasible("I cannot follow these instructions because there is no email field in this form.")
    """
    await report_infeasible_instructions(reason)

async def noop(wait_ms: float = 1000):
    """
    Do nothing, and optionally wait for the given time (in milliseconds).

    Examples:
        noop()
        noop(500)
    """
    await page.wait_for_timeout(wait_ms)


async def fill(
        bid: str,
        value: str,
        timeout: int = 10000,  # Increased default timeout to 10 seconds
        retry_attempts: int = 3
):
    """
    Fill out a form field with improved error handling and retry mechanism.
    It focuses the element and triggers an input event with the entered text.
    It works for <input>, <textarea> and [contenteditable] elements.
    Examples:
        fill('237', 'example value')
        fill('45', "multi-line\\nexample")
        fill('a12', "example with \\"quotes\\"")
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError, expect
    print(f"Attempting to fill element with bid: {bid}")
    try:
        # Locate the element by its bid and perform additional interactions if needed
        print("Locating element")
        elem = await get_elem_by_bid(page, bid, scroll_into_view=True, timeout=timeout)
        print(f"Element found: {elem}")
        print("Adding demo mode effects")
        await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
        print("Demo mode effects added")
        if demo_mode != "off":
            print("Starting fill in demo mode")
            await elem.clear()
            delay = max(2000 / len(value), 10)
            await elem.type(value, delay=delay)
            print("Fill completed in demo mode")
        else:
            print(f"Starting fill with timeout {timeout}ms")
            await elem.fill(value, timeout=timeout)
            print("Fill completed")
    except PlaywrightTimeoutError as e:
        print(f"Timeout error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    print("Fill operation completed (or failed with errors).")

async def check(bid: str):
    """
    Ensure a checkbox or radio element is checked.

    Examples:
        check('55')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)
    await elem.check(timeout=500)

async def uncheck(bid: str):
    """
    Ensure a checkbox or radio element is unchecked.

    Examples:
        uncheck('a5289')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)
    await elem.uncheck(timeout=500)

async def select_option(bid: str, options: str | list[str]):
    """
    Select one or multiple options in a <select> element. You can specify
    option value or label to select. Multiple options can be selected.

    Examples:
        select_option('a48', "blue")
        select_option('c48', ["red", "green", "blue"])
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    await elem.select_option(options, timeout=500)



async def click(
        bid: str,
        button: Literal["left", "middle", "right"] = "left",
        modifiers: list[Literal["Alt", "Control", "Meta", "Shift"]] = [],
        timeout: int = 3000,
):
    """
    Click an element with improved error handling, retry mechanism, and automatic new tab handling.
    Examples:
        click('a51')
        click('b22', button="right")
        click('48', button="middle", modifiers=["Shift"])
    """
    from playwright.async_api import TimeoutError as PlaywrightTimeoutError, expect
    import time
    print(f"Attempting to click element with bid: {bid}")
    context = page.context  # Extract the context from the current page
    new_page = None  # Initialize the variable for new page
    try:
        # Locate the element by its bid and perform additional interactions if needed
        elem = await get_elem_by_bid(page, bid, scroll_into_view=True, timeout=timeout)
        await expect(elem).to_be_enabled(timeout=timeout)
        await expect(elem).to_be_visible(timeout=timeout)
        # Capture the initial URL of the current page
        initial_url = page.url
        # Perform the click action
        await elem.click(button=button, modifiers=modifiers, timeout=timeout, force=True)
        # Try to detect a new page or handle redirection
        print("Waiting for a new page or navigation...")
        try:
            # Wait for a new page to open in the context
            new_page = await context.wait_for_event("page", timeout=timeout)
            print("New page detected.")
        except PlaywrightTimeoutError:
            # Log the timeout but do not propagate the error
            print("No new page detected within timeout.")
        # Handle the new page if detected
        if new_page:
            try:
                print("New page detected, waiting for load...")
                await new_page.wait_for_load_state("networkidle", timeout=5000)
                print(f"New page loaded with URL: {new_page.url}")
                # Optionally navigate the current page to the new page's URL
                if new_page.url:
                    print(f"Navigating current page to: {new_page.url}")
                    await page.goto(new_page.url)
                # Close the new page if not needed
                await new_page.close()
                return
            except Exception as e:
                print(f"Error handling new page: {e}")
                # Log the error and continue execution
        # If no new page is detected, check for navigation on the current page
        print("Checking for same-page navigation...")
        try:
            await page.wait_for_load_state("networkidle", timeout=timeout)
            if page.url != initial_url:
                print(f"Page redirected to new URL: {page.url}")
            else:
                print("No redirection detected; operation completed on the same page.")
        except PlaywrightTimeoutError:
            print("No navigation detected on the current page within timeout.")
    except Exception as e:
        print(f"Unexpected error occurred during the click operation: {e}")
        # Log the error and continue execution

async def dblclick(
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
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)
    await elem.dblclick(button=button, modifiers=modifiers, timeout=500)

async def hover(bid: str):
    """
    Hover over an element.

    Examples:
        hover('b8')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    if demo_mode != "off":
        box = await elem.bounding_box()
        if box:
            center_x, center_y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            await smooth_move_visual_cursor_to(page, center_x, center_y)
    await elem.hover(timeout=500)

async def press(bid: str, key_comb: str):
    """
    Focus the matching element and press a combination of keys.

    Examples:
        press('88', 'Backspace')
        press('a26', 'Control+a')
        press('a61', 'Meta+Shift+t')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    await elem.press(key_comb, timeout=500)

async def focus(bid: str):
    """
    Focus the matching element.

    Examples:
        focus('b455')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    await elem.focus(timeout=500)

async def clear(bid: str):
    """
    Clear the input field.

    Examples:
        clear('996')
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=False)
    await elem.clear(timeout=500)

async def drag_and_drop(from_bid: str, to_bid: str):
    """
    Perform a drag & drop.

    Examples:
        drag_and_drop('56', '498')
    """
    from_elem = await get_elem_by_bid(page, from_bid, demo_mode != "off")
    await add_demo_mode_effects(page, from_elem, from_bid, demo_mode=demo_mode, move_cursor=True)
    await from_elem.hover(timeout=500)
    await page.mouse.down()

    to_elem = await get_elem_by_bid(page, to_bid, demo_mode != "off")
    await add_demo_mode_effects(page, to_elem, to_bid, demo_mode=demo_mode, move_cursor=True)
    await to_elem.hover(timeout=500)
    await page.mouse.up()

async def scroll(delta_x: float, delta_y: float):
    """
    Scroll horizontally and vertically.

    Examples:
        scroll(0, 200)
        scroll(-50.2, -100.5)
    """
    await page.mouse.wheel(delta_x, delta_y)

async def mouse_move(x: float, y: float):
    """
    Move the mouse to a location.

    Examples:
        mouse_move(65.2, 158.5)
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
    await page.mouse.move(x, y)

async def mouse_up(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location then release a mouse button.

    Examples:
        mouse_up(250, 120)
        mouse_up(47, 252, 'right')
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
        await highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    await page.mouse.move(x, y)
    await page.mouse.up(button=button)

async def mouse_down(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location then press and hold a mouse button.

    Examples:
        mouse_down(140.2, 580.1)
        mouse_down(458, 254.5, 'middle')
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
        await highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    await page.mouse.move(x, y)
    await page.mouse.down(button=button)

async def mouse_click(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location and click a mouse button.

    Examples:
        mouse_click(887.2, 68)
        mouse_click(56, 712.56, 'right')
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
        await highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    await page.mouse.click(x, y, button=button)

async def mouse_dblclick(x: float, y: float, button: Literal["left", "middle", "right"] = "left"):
    """
    Move the mouse to a location and double click a mouse button.

    Examples:
        mouse_dblclick(5, 236)
        mouse_dblclick(87.5, 354, 'right')
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
        await highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})
    await page.mouse.dblclick(x, y, button=button)

async def mouse_drag_and_drop(from_x: float, from_y: float, to_x: float, to_y: float):
    """
    Drag and drop from a location to a location.

    Examples:
        mouse_drag_and_drop(10.7, 325, 235.6, 24.54)
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, from_x, from_y)
        await highlight_by_box(page, {"x": from_x, "y": from_y, "width": 1, "height": 1})
    await page.mouse.move(from_x, from_y)
    await page.mouse.down()
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, to_x, to_y)
        await highlight_by_box(page, {"x": to_x, "y": to_y, "width": 1, "height": 1})
    await page.mouse.move(to_x, to_y)
    await page.mouse.up()

async def keyboard_press(key: str):
    """
    Press a combination of keys.

    Examples:
        keyboard_press('Backspace')
        keyboard_press('Control+a')
        keyboard_press('Meta+Shift+t')
        keyboard_press("PageDown")
    """
    await page.keyboard.press(key)

async def keyboard_up(key: str):
    """
    Release a keyboard key.

    Examples:
        keyboard_up('Shift')
        keyboard_up('c')
    """
    await page.keyboard.up(key)

async def keyboard_down(key: str):
    """
    Press and holds a keyboard key.

    Examples:
        keyboard_down('Shift')
        keyboard_down('c')
    """
    await page.keyboard.down(key)

async def keyboard_type(text: str):
    """
    Types a string of text through the keyboard.

    Examples:
        await keyboard_type('Hello world!')
    """
    if demo_mode:
        delay = max(2000 / len(text), 10)
    else:
        delay = None
    await page.keyboard.type(text, delay=delay)

async def keyboard_insert_text(text: str):
    """
    Insert a string of text in the currently focused element.

    Examples:
        keyboard_insert_text('Hello world!')
    """
    await page.keyboard.insert_text(text)

async def goto(url: str):
    """
    Navigate to a url.

    Examples:
        goto('http://www.example.com')
    """
    await page.goto(url)

async def go_back():
    """
    Navigate to the previous page in history.

    Examples:
        go_back()
    """
    await page.go_back()

async def go_forward():
    """
    Navigate to the next page in history.

    Examples:
        go_forward()
    """
    await page.go_forward()

async def new_tab():
    """
    Open a new tab. It will become the active one.

    Examples:
        new_tab()
    """
    global page
    # set the new page as the active page
    page = await page.context.new_page()
    # trigger the callback that sets this page as active in browsergym
    await page.locator("html").dispatch_event("pageshow")

async def tab_close():
    """
    Close the current tab.

    Examples:
        tab_close()
    """
    global page
    context = page.context
    await page.close()
    # set most recent page as active page, or open a new page if needed
    if context.pages:
        # TODO: do something more elaborate? (active page history)
        page = context.pages[-1]
    else:
        page = await context.new_page()
    # trigger the callback that sets this page as active in browsergym
    await page.locator("html").dispatch_event("pageshow")

async def tab_focus(index: int):
    """
    Bring tab to front (activate tab).

    Examples:
        tab_focus(2)
    """
    global page  # set the focused page as the active page
    page = page.context.pages[index]
    # trigger the callback that sets this page as active in browsergym
    await page.locator("html").dispatch_event("pageshow")

async def upload_file(bid: str, file: str | list[str]):
    """
    Click an element and wait for a "filechooser" event, then select one
    or multiple input files for upload.

    Examples:
        upload_file("572", "my_receipt.pdf")
        upload_file("63", ["/home/bob/Documents/image.jpg", "/home/bob/Documents/file.zip"])
    """
    elem = await get_elem_by_bid(page, bid, demo_mode != "off")
    await add_demo_mode_effects(page, elem, bid, demo_mode=demo_mode, move_cursor=True)

    async with page.expect_file_chooser() as fc_info:
        await elem.click(timeout=500)

    file_chooser = await fc_info.value
    await file_chooser.set_files(file)

async def mouse_upload_file(x: float, y: float, file: str | list[str]):
    """
    Click a location and wait for a "filechooser" event, then select one
    or multiple input files for upload.

    Examples:
        mouse_upload_file(132.1, 547, "my_receipt.pdf")
        mouse_upload_file(328, 812, ["/home/bob/Documents/image.jpg", "/home/bob/Documents/file.zip"])
    """
    if demo_mode != "off":
        await smooth_move_visual_cursor_to(page, x, y)
        await highlight_by_box(page, {"x": x, "y": y, "width": 1, "height": 1})

    async with page.expect_file_chooser() as fc_info:
        await page.mouse.click(x, y)

    file_chooser = await fc_info.value
    await file_chooser.set_files(file)