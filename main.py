import os
import sys
from itertools import permutations
from PIL import Image
import numpy as np
from concurrent.futures import ProcessPoolExecutor


def save_image(image, filename, image_format, compression):
    try:
        print(f"Attempting to save image to {filename}")
        if image_format == 'webp':
            image.save(filename, format="webp", lossless=compression)
        else:
            image.save(filename)
        print(f"Successfully saved image: {filename}")
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


def generate_tween_frames(image1, image2, num_tween_frames, base_filename, start_index, final_dir, image_format,
                          compression):
    img_array1 = np.array(image1)
    img_array2 = np.array(image2)
    tween_filenames = []

    for i in range(1, num_tween_frames + 1):
        weight = i / (num_tween_frames + 1)
        tween_img_array = (1 - weight) * img_array1 + weight * img_array2
        tween_img = Image.fromarray(np.uint8(tween_img_array))
        tween_filename = os.path.join(final_dir, f"{base_filename}_{start_index + i:04d}.{image_format}")
        save_image(tween_img, tween_filename, image_format, compression)
        tween_filenames.append(tween_filename)
        print(f"Saved tween frame: {tween_filename}")

    return tween_filenames


def resize_image(image, width):
    if width == 0:
        return image
    ratio = width / float(image.size[0])
    height = int((float(image.size[1]) * float(ratio)))
    return image.resize((width, height), Image.LANCZOS)


def process_tween_frames(args):
    return generate_tween_frames(*args)


def process_images(image_path, num_tween_frames, image_format, compression, resize_width, repeat_frames):
    image = Image.open(image_path)
    base_filename = os.path.splitext(os.path.basename(image_path))[0]

    # Resize image if required
    image = resize_image(image, resize_width)

    output_dir = os.path.join(os.path.dirname(image_path), f"{base_filename}_shuffled")
    final_dir = os.path.join(os.path.dirname(image_path), f"{base_filename}_shuffled_tweens")

    if not os.path.exists(output_dir):
        print(f"Creating directory: {output_dir}")
        os.makedirs(output_dir)

    if not os.path.exists(final_dir):
        print(f"Creating directory: {final_dir}")
        os.makedirs(final_dir)

    channel_orders = generate_channel_orders()
    generated_filenames = []

    frame_index = 0

    for idx, order in enumerate(channel_orders):
        new_filename = os.path.join(output_dir, f"{base_filename}_{frame_index:04d}.{image_format}")
        save_image_with_new_channels(image, order, new_filename, image_format, compression)
        generated_filenames.append(new_filename)
        frame_index += 1

    # Ensure all generated files exist before proceeding
    for filename in generated_filenames:
        if not os.path.exists(filename):
            print(f"File not found after generation: {filename}")
            return

    # Load the generated images
    generated_images = []
    for filename in generated_filenames:
        print(f"Loading generated image: {filename}")
        try:
            generated_images.append(Image.open(filename))
        except FileNotFoundError:
            print(f"File not found during loading: {filename}")
            return

    # Prepare arguments for tween frame generation
    tween_args_list = []
    num_generated_images = len(generated_images)

    for i in range(num_generated_images):
        current_frame = generated_images[i]

        # Save the current generated frame multiple times (repeat_frames)
        for _ in range(repeat_frames):
            current_generated_filename = os.path.join(final_dir, f"{base_filename}_{frame_index:04d}.{image_format}")
            save_image(current_frame, current_generated_filename, image_format, compression)
            frame_index += 1

        # Calculate and save tween frames to the original RGB image
        tween_args_list.append(
            (current_frame, image, num_tween_frames, base_filename, frame_index, final_dir, image_format, compression))
        frame_index += num_tween_frames

        # Save the original RGB image multiple times (repeat_frames)
        for _ in range(repeat_frames):
            original_filename = os.path.join(final_dir, f"{base_filename}_{frame_index:04d}.{image_format}")
            save_image(image, original_filename, image_format, compression)
            frame_index += 1

        # Calculate and save tween frames from the original RGB image to the next generated frame
        next_frame = generated_images[(i + 1) % num_generated_images] if i + 1 < num_generated_images else current_frame
        tween_args_list.append(
            (image, next_frame, num_tween_frames, base_filename, frame_index, final_dir, image_format, compression))
        frame_index += num_tween_frames

    # Generate tween frames in parallel
    with ProcessPoolExecutor() as executor:
        for tween_filenames in executor.map(process_tween_frames, tween_args_list):
            for tween_filename in tween_filenames:
                print(f"Confirmed saved tween frame: {tween_filename}")


def main():
    if len(sys.argv) != 7:
        print(
            "Usage: python rearrange_channels_with_inversion.py <image_path> <num_tween_frames> <image_format> <compression> <resize_width> <repeat_frames>")
        print("Format options: png, webp")
        print("Compression: 0 for lossy WebP, 1 for lossless WebP (ignored for PNG)")
        print("Resize width: 0 for no resizing")
        print("Repeat frames: number of times to repeat each frame")
        sys.exit(1)

    image_path = sys.argv[1]
    num_tween_frames = int(sys.argv[2])
    image_format = sys.argv[3]
    compression = bool(int(sys.argv[4]))
    resize_width = int(sys.argv[5])
    repeat_frames = int(sys.argv[6])

    if image_format not in ['png', 'webp']:
        print("Invalid format. Supported formats are png and webp.")
        sys.exit(1)

    process_images(image_path, num_tween_frames, image_format, compression, resize_width, repeat_frames)


if __name__ == "__main__":
    main()
