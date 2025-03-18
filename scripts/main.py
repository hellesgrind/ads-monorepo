from image_analyze import (
    analyze_image,
    merge_horizontal_boxes,
    draw_boxes,
    merge_vertical_boxes,
)
from text_rendering import get_layout_from_image
from composition import render_html_to_image


def process_image(input_path: str, output_path: str, html_path: str, boxes_path: str):
    print(f"Starting analysis of: {input_path}")

    analysis = analyze_image(input_path)
    print(f"Analysis: {analysis}")
    text_blocks = analysis.text_blocks
    text_blocks = merge_horizontal_boxes(text_blocks)
    text_blocks = merge_vertical_boxes(text_blocks)

    print("Drawing boxes on original image")
    draw_boxes(input_path, text_blocks, boxes_path)
    print(f"Image with boxes saved to: {boxes_path}")

    # print("Getting HTML layout from Claude")
    # html_layout = get_layout_from_image(
    #     input_path,
    #     analysis.width,
    #     analysis.height,
    #     [block.model_dump() for block in analysis.text_blocks],
    # )
    # html_layout = open(html_path).read()

    # print("Rendering HTML to image")
    # render_html_to_image(html_layout, output_path, analysis.width, analysis.height)
    # print(f"HTML rendered to image and saved to: {output_path}")


if __name__ == "__main__":
    input_path = "example.jpeg"
    output_path = "result.png"
    html_path = "layout.html"
    boxes_path = "boxes.jpeg"
    process_image(input_path, output_path, html_path, boxes_path)
