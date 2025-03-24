import os
from image_analyze import (
    analyze_image,
    merge_horizontal_boxes,
    draw_boxes,
    merge_vertical_boxes,
    clean_text_blocks,
    identify_text_blocks_fonts,
    correct_text_blocks_coordinates,
)
from image_generation import remove_text_from_image
from text_rendering import create_html_layout


def process_image(input_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)
    print(f"Starting analysis of: {input_path}")
    analysis = analyze_image(input_path)
    text_blocks = analysis.text_blocks
    text_blocks = merge_horizontal_boxes(text_blocks)
    text_blocks = merge_vertical_boxes(text_blocks)
    text_blocks = clean_text_blocks(text_blocks)
    print("Drawing boxes on original image")
    image_with_boxes_path = os.path.join(output_dir, "image_with_boxes.jpeg")
    draw_boxes(input_path, text_blocks, image_with_boxes_path)
    print(f"Image with boxes saved to: {image_with_boxes_path}")
    text_blocks_with_fonts = identify_text_blocks_fonts(input_path, text_blocks)
    corrected_text_blocks = correct_text_blocks_coordinates(
        input_path, text_blocks_with_fonts
    )
    print("Drawing boxes on original image")
    image_with_corrected_boxes_path = os.path.join(
        output_dir, "image_with_corrected_boxes.jpeg"
    )
    draw_boxes(input_path, corrected_text_blocks, image_with_corrected_boxes_path)
    print(f"Image with corrected boxes saved to: {image_with_corrected_boxes_path}")

    cleaned_image_path = os.path.join(output_dir, "cleaned_image.png")
    # remove_text_from_image(
    #     image_path=input_path,
    #     text_blocks=analysis.text_blocks,
    #     output_path=cleaned_image_path,
    # )
    print(f"Cleaned image saved to: {cleaned_image_path}")
    html_layout = create_html_layout(input_path, corrected_text_blocks)
    # html_layout = html_layout.format(image_path=cleaned_image_path)
    html_layout_path = os.path.join(output_dir, "layout.html")
    with open(html_layout_path, "w") as f:
        f.write(html_layout)
    print(f"HTML layout saved to: {html_layout_path}")


    # changed_image_path = os.path.join(output_dir, "changed_image.png")
    # regenerate_image(cleaned_image_path, changed_image_path)
    # print(f"Changed image saved to: {changed_image_path}")

    # print("Getting HTML layout from Claude")
    # initial_html_path = os.path.join(output_dir, "initial_layout.html")
    # initial_html = get_layout_from_image(
    #     input_path,
    #     analysis.width,
    #     analysis.height,
    #     text_blocks,
    # )
    # with open(initial_html_path, "w") as f:
    #     f.write(initial_html)
    # print(f"Initial HTML saved to: {initial_html_path}")
    # return initial_html


if __name__ == "__main__":
    input_path = "creo_01.png"
    output_dir = "result"
    process_image(input_path, output_dir)
