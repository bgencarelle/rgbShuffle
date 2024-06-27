import os
import sys
from itertools import permutations
import numpy as np
from PIL import Image, ImageOps


def save_image(image, filename, image_format):
    try:
        if image_format == 'webp':
            image.save(filename, format="webp", quality=95, lossless=False)
        else:
            image.save(filename)
    except Exception as e:
        print(f"Error saving image {filename}: {e}")


def save_image_with_new_channels(image, channels_order, filename, image_format):
    img_array = np.array(image)
    channel_map = {'R': 0, 'G': 1, 'B': 2}
    new_img_array = np.zeros_like(img_array)

    for i, ch in enumerate(channels_order):
        if ch.endswith('inv'):
            channel_idx = channel_map[ch[0]]
            new_img_array[..., i] = 255 - img_array[..., channel_idx]
        else:
            channel_idx = channel_map[ch]
            new_img_array[..., i] = img_array[..., channel_idx]

    new_image = Image.fromarray(new_img_array)
    save_image(new_image, filename, image_format)


def generate_channel_orders():
    base_channels = ['R', 'G', 'B']
    all_orders = []

    for perm in permutations(base_channels, 3):
        all_orders.append(perm)
        all_orders.append(tuple(ch + 'inv' for ch in perm))

    # Sort orders alphabetically
    all_orders = sorted(all_orders, key=lambda x: ''.join(x))

    return all_orders


def letterbox_image(image, target_size):
    """
    Resize and letterbox the image to fit within the specified size.
    """
    return ImageOps.fit(image, target_size, Image.LANCZOS, 0, (0.5, 0.5))


def resize_images(input_folder, output_folder, resize_width):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    valid_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.webp', '.bmp')
    resized_images = []

    for root, _, files in os.walk(input_folder):
        for file_name in sorted(files):
            file_path = os.path.join(root, file_name)
            if os.path.isfile(file_path) and file_path.lower().endswith(valid_extensions):
                image = Image.open(file_path)
                target_height = int(resize_width * image.size[1] / image.size[0])
                resized_image = letterbox_image(image, (resize_width, target_height))
                relative_path = os.path.relpath(file_path, input_folder)
                resized_file_path = os.path.join(output_folder, relative_path)
                os.makedirs(os.path.dirname(resized_file_path), exist_ok=True)
                resized_image.save(resized_file_path)
                resized_images.append(resized_file_path)

    return resized_images


def process_images(image_path, image_format, base_folder_name, file_index, parent_output_folder):
    image = Image.open(image_path)

    target_size = image.size
    image = letterbox_image(image, target_size)

    channel_orders = generate_channel_orders()

    for order in channel_orders:
        order_str = ''.join(order)
        output_dir = os.path.join(parent_output_folder,
                                  f"{base_folder_name}_{target_size[0]}x{target_size[1]}_{order_str}")

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        new_filename = os.path.join(output_dir, f"{base_folder_name}_{order_str}_{file_index:06d}.{image_format}")
        save_image_with_new_channels(image, order, new_filename, image_format)


def main():
    if len(sys.argv) != 4:
        print("Usage: python shuffle.py <folder_path> <image_format> <resize_width>")
        print("Format options: png, webp")
        sys.exit(1)

    folder_path = sys.argv[1]
    image_format = sys.argv[2].lower()
    resize_width = int(sys.argv[3])

    if image_format not in ['png', 'webp']:
        print("Invalid format. Supported formats are png and webp.")
        sys.exit(1)

    base_folder_name = os.path.basename(os.path.normpath(folder_path))
    parent_folder = os.path.dirname(folder_path)
    parent_output_folder = os.path.join(parent_folder, f"{base_folder_name}_{resize_width}px_output")

    if not os.path.exists(parent_output_folder):
        os.makedirs(parent_output_folder)

    resized_folder = os.path.join(parent_output_folder, "resized")

    # Resize images and get the paths of resized images
    resized_images = resize_images(folder_path, resized_folder, resize_width)

    for file_index, file_path in enumerate(resized_images):
        process_images(file_path, image_format, base_folder_name, file_index, parent_output_folder)


if __name__ == "__main__":
    main()
