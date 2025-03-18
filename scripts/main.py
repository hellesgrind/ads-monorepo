from image_analyze import (
    analyze_image,
    merge_horizontal_boxes,
    draw_boxes,
    merge_vertical_boxes,
)
from text_rendering import get_layout_from_image
from composition import render_html_to_image
from image_generation import remove_text_from_image, redux_image

def process_image(input_path: str, output_path: str, html_path: str, boxes_path: str):
    print(f"Starting analysis of: {input_path}")

    analysis = analyze_image(input_path)
    text_blocks = analysis.text_blocks
    text_blocks = merge_horizontal_boxes(text_blocks)
    text_blocks = merge_vertical_boxes(text_blocks)

    # print("Drawing boxes on original image")
    # draw_boxes(input_path, text_blocks, boxes_path)
    # print(f"Image with boxes saved to: {boxes_path}")
    # cleaned_image_path = "cleaned_image.png"
    # remove_text_from_image(
    #     image_path=input_path,
    #     text_blocks=analysis.text_blocks,
    #     output_path=cleaned_image_path,
    # )
    # print(f"Cleaned image saved to: {cleaned_image_path}")
    # changed_image_path = "changed_image.png"
    # redux_image(cleaned_image_path, changed_image_path)
    # print(f"Changed image saved to: {changed_image_path}")
    # # print("Getting HTML layout from Claude")
    html_layout = get_layout_from_image(
        input_path,
        analysis.width,
        analysis.height,
        text_blocks,
    )
    with open(html_path, "w") as f:
        f.write(html_layout)
    # # html_layout = open(html_path).read()

    # print("Rendering HTML to image")
    # render_html_to_image(html_layout, output_path, analysis.width, analysis.height)
    # print(f"HTML rendered to image and saved to: {output_path}")


if __name__ == "__main__":
    input_path = "example.png"
    output_path = "result.png"
    html_path = "layout.html"
    boxes_path = "boxes.jpeg"
    process_image(input_path, output_path, html_path, boxes_path)
