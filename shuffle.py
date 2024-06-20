import os
import sys
from itertools import permutations
import numpy as np
from PIL import Image


def save_image(image, filename, image_format, compression):
    try:
        if image_format == 'webp':
            image.save(filename, format="webp", lossless=compression)
        else:
            image.save(filename)
    except Exception as e:
        print(f"Error saving image {filename}: {e}")


def save_image_with_new_channels(image, channels_order, filename, image_format, compression):
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
    save_image(new_image, filename, image_format, compression)


def generate_channel_orders():
    base_channels = ['R', 'G', 'B']
    all_channels = base_channels + [ch + 'inv' for ch in base_channels]
    permutations_list = list(permutations(all_channels, 3))
    return permutations_list


def resize_image(image, width):
    if width == 0:
        return image
    ratio = width / float(image.size[0])
    height = int((float(image.size[1]) * float(ratio)))
    return image.resize((width, height), Image.LANCZOS)


def process_images(image_path, image_format, compression, resize_width):
    image = Image.open(image_path)
    base_filename = os.path.splitext(os.path.basename(image_path))[0]

    # Resize image if required
    image = resize_image(image, resize_width)

    shuffled_dir = os.path.join(os.path.dirname(image_path), f"{base_filename}_shuffled")

    if not os.path.exists(shuffled_dir):
        os.makedirs(shuffled_dir)

    channel_orders = generate_channel_orders()
    frame_index = 0

    for idx, order in enumerate(channel_orders):
        order_str = ''.join(order)
        new_filename = os.path.join(shuffled_dir, f"{base_filename}_{frame_index:04d}_{order_str}_0.{image_format}")
        save_image_with_new_channels(image, order, new_filename, image_format, compression)
        frame_index += 1


def main():
    if len(sys.argv) != 5:
        print("Usage: python generate_shuffled_images.py <image_path> <image_format> <compression> <resize_width>")
        print("Format options: png, webp")
        print("Compression: 0 for lossy WebP, 1 for lossless WebP (ignored for PNG)")
        print("Resize width: 0 for no resizing")
        sys.exit(1)

    image_path = sys.argv[1]
    image_format = sys.argv[2]
    compression = bool(int(sys.argv[3]))
    resize_width = int(sys.argv[4])

    if image_format not in ['png', 'webp']:
        print("Invalid format. Supported formats are png and webp.")
        sys.exit(1)

    process_images(image_path, image_format, compression, resize_width)


if __name__ == "__main__":
    main()
