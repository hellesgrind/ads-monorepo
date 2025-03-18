from image_analyze import (
    analyze_image,
    merge_horizontal_boxes,
    draw_boxes,
    merge_vertical_boxes,
)
from text_rendering import get_layout_from_image
from image_generation import remove_text_from_image, regenerate_image

def process_image(input_path: str, output_path: str, html_path: str, boxes_path: str):
    print(f"Starting analysis of: {input_path}")

    analysis = analyze_image(input_path)
    text_blocks = analysis.text_blocks
    text_blocks = merge_horizontal_boxes(text_blocks)
    text_blocks = merge_vertical_boxes(text_blocks)

    print("Drawing boxes on original image")
    draw_boxes(input_path, text_blocks, boxes_path)
    print(f"Image with boxes saved to: {boxes_path}")
    cleaned_image_path = "cleaned_image.png"
    remove_text_from_image(
        image_path=input_path,
        text_blocks=analysis.text_blocks,
        output_path=cleaned_image_path,
    )
    print(f"Cleaned image saved to: {cleaned_image_path}")
    changed_image_path = "changed_image.png"
    regenerate_image(cleaned_image_path, changed_image_path)
    print(f"Changed image saved to: {changed_image_path}")
    print("Getting HTML layout from Claude")
    initial_html_path = "initial_layout.html"
    initial_html = get_layout_from_image(
        input_path,
        analysis.width,
        analysis.height,
        text_blocks,
    )
    with open(initial_html_path, "w") as f:
        f.write(initial_html)
    return initial_html

if __name__ == "__main__":
    input_path = "example.png"
    output_path = "result.png"
    html_path = "layout.html"
    boxes_path = "boxes.jpeg"
    process_image(input_path, output_path, html_path, boxes_path)
