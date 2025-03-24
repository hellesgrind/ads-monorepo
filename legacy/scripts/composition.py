from playwright.sync_api import sync_playwright
import os


def render_html_to_image(html_content: str, output_path: str, width: int, height: int):
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": width, "height": height})

        page.set_content(html_content)
        page.wait_for_load_state("networkidle")
        page.screenshot(path=output_path)
        browser.close()


if __name__ == "__main__":
    html = "<div>Test</div>"
    output = "test.png"
    width = 1920
    height = 1080
    render_html_to_image(html, output, width, height)
