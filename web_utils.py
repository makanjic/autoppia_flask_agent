# take from autoppia_iwa

import difflib
from io import BytesIO
from typing import Any, Dict, List, Tuple

from bs4 import BeautifulSoup, Comment
from PIL import Image
from playwright.async_api import async_playwright
from xmldiff import main

# XXX: UIParserServer does nothing now
# from autoppia_iwa.src.llms.infrastructure.ui_parser_service import UIParserService


# async def get_html_and_screenshot(page_url: str) -> Tuple[str, str, Image.Image, str]:
async def get_html_contents(page_url: str) -> str:
    """
    Navigates to page_url using Playwright in headless mode, extracts & cleans HTML,
    captures a screenshot, and uses UIParserService to generate a textual summary
    of that screenshot. Returns (cleaned_html, screenshot_description).
    """
    # screenshot = None
    # screenshot_description = ""
    # cleaned_html = ""
    raw_html = ""

    try:
        async with async_playwright() as p:
            browser_type = p.chromium
            browser = await browser_type.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()
            await page.goto(page_url, timeout=60000)

            ## Extract raw HTML and clean it
            raw_html = await page.content()
            # cleaned_html = clean_html(raw_html)

            ## Capture screenshot in memory
            # screenshot_bytes = await page.screenshot()
            # screenshot = Image.open(BytesIO(screenshot_bytes)).convert("RGB")

            ## Generate textual summary of the screenshot
            # ui_parser = UIParserService()
            # screenshot_description = ui_parser.summarize_image(screenshot)

            await context.close()
            await browser.close()

    except Exception as e:
        print(f"Error during HTML extraction or screenshot processing: {e}")
        # return raw_html, cleaned_html, None, screenshot_description
        return ""

    # return raw_html, cleaned_html, screenshot, screenshot_description
    return raw_html


def sync_extract_html(page_url: str) -> str:
    """
    Uses Playwright in sync mode to extract HTML from a page.
    Adjust if your environment doesn't support sync Playwright.
    """
    from playwright.sync_api import sync_playwright

    launch_options = {"headless": True, "args": ["--start-maximized"]}
    with sync_playwright() as p:
        browser_type = p.chromium
        browser = browser_type.launch(**launch_options)
        context = browser.new_context()
        page = context.new_page()
        page.goto(page_url)
        html = page.content()
        context.close()
        browser.close()
    return html


async def async_extract_html(page_url: str) -> str:
    """
    Uses Playwright in async mode to extract raw HTML from a page.
    """
    launch_options = {"headless": True, "args": ["--start-maximized"]}
    async with async_playwright() as p:
        browser_type = p.chromium
        browser = await browser_type.launch(**launch_options)
        context = await browser.new_context()
        page = await context.new_page()
        await page.goto(page_url)
        html = await page.content()
        await context.close()
        await browser.close()
    return html


def clean_html(html_content: str) -> str:
    """
    Removes scripts, styles, hidden tags, inline event handlers, etc.,
    returning a 'clean' version of the DOM.
    This version is exception resistant.
    """
    try:
        soup = BeautifulSoup(html_content, "html.parser")
    except Exception:
        return ""

    # Remove scripts, styles, metas, links, noscript
    try:
        for tag in soup(["script", "style", "noscript", "meta", "link"]):
            try:
                tag.decompose()
            except Exception:
                pass
    except Exception:
        pass

    # Remove HTML comments
    try:
        for comment in soup.find_all(string=lambda t: isinstance(t, Comment)):
            try:
                comment.extract()
            except Exception:
                pass
    except Exception:
        pass

    # Remove hidden elements and inline events
    try:
        for tag in soup.find_all(True):
            try:
                if tag.has_attr("style") and tag["style"]:
                    try:
                        style_lc = tag["style"].lower()
                    except Exception:
                        style_lc = ""
                    if "display: none" in style_lc or "visibility: hidden" in style_lc:
                        try:
                            tag.decompose()
                        except Exception:
                            pass
                        continue
                if tag.has_attr("hidden"):
                    try:
                        tag.decompose()
                    except Exception:
                        pass
                    continue
                # Remove inline event handlers and style/id/class attributes
                for attr in list(tag.attrs):
                    if attr.startswith("on") or attr in ["class", "id", "style"]:
                        try:
                            del tag[attr]
                        except Exception:
                            pass
            except Exception:
                pass
    except Exception:
        pass

    # Remove empty tags
    try:
        for tag in soup.find_all():
            try:
                if not tag.text.strip() and not tag.find_all():
                    tag.decompose()
            except Exception:
                pass
    except Exception:
        pass

    # Return the cleaned HTML
    try:
        clean_soup = soup.body if soup.body else soup
        return clean_soup.prettify()
    except Exception:
        return ""


def detect_interactive_elements(cleaned_html: str) -> Dict[str, Any]:
    """
    Inspects the cleaned HTML to find possible interactive elements:
      - forms (with their inputs)
      - buttons or anchors with text
      - textareas, selects, etc.
    Returns a dict summarizing them for LLM usage, e.g.:
    {
      "forms": [
        {"fields": ["name", "email", "message"]}
      ],
      "buttons": ["Send", "Submit"],
      "links": ["Home", "Applications", "Overview", ...]
    }
    """
    summary = {"forms": [], "buttons": [], "links": []}
    soup = BeautifulSoup(cleaned_html, "html.parser")
    # Forms and their fields
    for form in soup.find_all("form"):
        form_info = []
        for inp in form.find_all(["input", "textarea", "select"]):
            placeholder = inp.get("placeholder") or inp.get("name") or inp.get("type")
            if placeholder:
                form_info.append(placeholder)
        summary["forms"].append({"fields": form_info})
    # Buttons (including input[type=submit])
    for btn in soup.find_all(["button", "input"], type="submit"):
        text = btn.text.strip() or btn.get("value") or "Submit"
        if text:
            summary["buttons"].append(text)
    # Links (anchor text)
    for a in soup.find_all("a"):
        link_text = a.text.strip()
        if link_text:
            summary["links"].append(link_text)
    return summary


def generate_html_differences(html_list: List[str]) -> List[str]:
    """Generate a list of initial HTML followed by diffs between consecutive HTMLs."""
    if not html_list:
        return []

    diffs = [html_list[0]]
    prev_html = html_list[0]

    for current_html in html_list[1:]:
        prev_lines = prev_html.splitlines(keepends=True)
        current_lines = current_html.splitlines(keepends=True)
        diff_generator = difflib.unified_diff(prev_lines, current_lines, lineterm='')
        diff_str = ''.join(diff_generator)
        if diff_str:
            diffs.append(diff_str)
        prev_html = current_html

    return diffs


def generate_html_differences_with_xmldiff(html_list: List[str]) -> List[str]:
    """Generate a list of initial HTML followed by diffs between consecutive HTMLs using xmldiff."""
    if not html_list:
        return []

    diffs = [html_list[0]]
    prev_html = html_list[0]

    for current_html in html_list[1:]:
        differences = main.diff_texts(prev_html, current_html)

        diff_str = "\n".join([str(diff) for diff in differences])
        if diff_str:
            diffs.append(diff_str)

        prev_html = current_html

    return diffs
