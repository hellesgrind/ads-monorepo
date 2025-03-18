from image_analyze import analyze_image, merge_horizontal_boxes
from text_rendering import get_layout_from_image
from composition import render_html_to_image


def process_image(input_path: str, output_path: str, html_path: str):
    print(f"Starting analysis of: {input_path}")

    analysis = analyze_image(input_path)

    print("Getting HTML layout from Claude")
    html_layout = get_layout_from_image(
        input_path,
        analysis.width,
        analysis.height,
        [block.model_dump() for block in analysis.text_blocks],
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_layout)
    print(f"HTML layout saved to: {html_path}")

    print("Rendering final image")
    result_image = render_html_to_image(html_layout, analysis.width, analysis.height)
    result_image.save(output_path)
    print(f"Result saved to: {output_path}")


if __name__ == "__main__":
    input_path = "example.jpeg"
    output_path = "result.png"
    html_path = "layout.html"
    process_image(input_path, output_path, html_path)
