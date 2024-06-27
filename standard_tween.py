import os
import sys
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor


def save_image(image, filename, image_format):
    try:
        if image_format == 'webp':
            image.save(filename, format="webp", quality=95, lossless=False)
        else:
            image.save(filename)
    except Exception as e:
        print(f"Error saving image {filename}: {e}")


def generate_tween_frames(image1_path, image2_path, num_tween_frames, start_index, output_folder, image_format):
    try:
        image1 = Image.open(image1_path)
        image2 = Image.open(image2_path)
    except Exception as e:
        print(f"Error opening image {image1_path} or {image2_path}: {e}")
        return []

    img_array1 = np.array(image1)
    img_array2 = np.array(image2)
    tween_filenames = []

    for i in range(1, num_tween_frames + 1):
        weight = i / (num_tween_frames + 1)
        tween_img_array = (1 - weight) * img_array1 + weight * img_array2
        tween_img = Image.fromarray(np.uint8(tween_img_array))
        tween_filename = os.path.join(output_folder, f"{start_index:06d}.{image_format}")
        save_image(tween_img, tween_filename, image_format)
        tween_filenames.append(tween_filename)
        start_index += 1

    return tween_filenames


def process_tween_images(input_folder, num_tween_frames, image_format, output_folder):
    valid_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.webp', '.bmp')
    input_files = sorted([f for f in os.listdir(input_folder) if
                          os.path.isfile(os.path.join(input_folder, f)) and f.lower().endswith(valid_extensions)])
    input_images = [os.path.join(input_folder, f) for f in input_files]

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    frame_index = 0
    tasks = []

    with ProcessPoolExecutor() as executor:
        for i in range(len(input_images) - 1):
            current_frame = input_images[i]
            next_frame = input_images[i + 1]

            # Save the current frame
            current_filename = os.path.join(output_folder, f"{frame_index:06d}.{image_format}")
            try:
                save_image(Image.open(current_frame), current_filename, image_format)
            except Exception as e:
                print(f"Error saving image {current_filename}: {e}")
            frame_index += 1

            # Generate tween frames
            task = executor.submit(generate_tween_frames, current_frame, next_frame, num_tween_frames, frame_index,
                                   output_folder, image_format)
            tasks.append(task)
            frame_index += num_tween_frames

        for task in tasks:
            task.result()

    # Save the last frame
    last_filename = os.path.join(output_folder, f"{frame_index:06d}.{image_format}")
    try:
        save_image(Image.open(input_images[-1]), last_filename, image_format)
    except Exception as e:
        print(f"Error saving image {last_filename}: {e}")


def main():
    if len(sys.argv) != 4:
        print("Usage: python tween.py <input_folder> <num_tween_frames> <image_format>")
        print("Format options: png, webp")
        sys.exit(1)

    input_folder = sys.argv[1]
    num_tween_frames = int(sys.argv[2])
    image_format = sys.argv[3].lower()

    if image_format not in ['png', 'webp']:
        print("Invalid format. Supported formats are png and webp.")
        sys.exit(1)

    output_folder = os.path.join(os.path.dirname(input_folder), f"{os.path.basename(input_folder)}_tweens")

    process_tween_images(input_folder, num_tween_frames, image_format, output_folder)


if __name__ == "__main__":
    main()
