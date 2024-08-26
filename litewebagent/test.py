from playwright.sync_api import sync_playwright, Playwright
import time

def run(playwright: Playwright, url):
    firefox = playwright.firefox
    browser = firefox.launch(headless=False)
    page = browser.new_page()
    page.goto(url)
    time.sleep(5)
    #page.goto("https://www.airbnb.com/s/San-Francisco/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2024-09-01&monthly_length=3&monthly_end_date=2024-12-01&price_filter_input_type=2&channel=EXPLORE&source=structured_search_input_header&search_type=search_query")
    #page.goto("https://www.theverge.com")
    print(page.main_frame)
    print(page.main_frame.child_frames)
    dump_frame_tree(page.main_frame, "")
    browser.close()

def dump_frame_tree(frame, indent):
    print(indent + frame.name + '@' + frame.url)
    for child in frame.child_frames:
        dump_frame_tree(child, indent + "    ")

with sync_playwright() as playwright:
    run(playwright, "https://www.amazon.com/")
    run(playwright, "https://www.theverge.com")
    run(playwright, "https://www.airbnb.com/s/San-Francisco/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&monthly_start_date=2024-09-01&monthly_length=3&monthly_end_date=2024-12-01&price_filter_input_type=2&channel=EXPLORE&source=structured_search_input_header&search_type=search_query")
    run(playwright, "https://www.airbnb.com/")