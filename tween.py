import os
import sys
import numpy as np
from PIL import Image
from concurrent.futures import ProcessPoolExecutor


def save_image(image, filename, image_format, compression):
    try:
        if image_format == 'webp':
            image.save(filename, format="webp", lossless=compression)
        else:
            image.save(filename)
    except Exception as e:
        print(f"Error saving image {filename}: {e}")


def generate_tween_frames(image1, image2, num_tween_frames, start_index, base_filename, final_dir, image_format,
                          compression, counter):
    img_array1 = np.array(image1)
    img_array2 = np.array(image2)
    tween_filenames = []

    for i in range(1, num_tween_frames + 1):
        weight = i / (num_tween_frames + 1)
        tween_img_array = (1 - weight) * img_array1 + weight * img_array2
        tween_img = Image.fromarray(np.uint8(tween_img_array))
        tween_filename = os.path.join(final_dir,
                                      f"{base_filename}_{start_index:06d}_tween_{counter:06d}.{image_format}")
        tween_filenames.append((tween_img, tween_filename))
        start_index += 1  # Increment frame index for each tween frame
        counter += 1  # Increment counter for each tween frame

    return tween_filenames, counter


def resize_image(image, width):
    ratio = width / float(image.size[0])
    height = int((float(image.size[1]) * float(ratio)))
    return image.resize((width, height), Image.LANCZOS)


def setup_output_folder(center_image_path, input_folder):
    base_filename = os.path.splitext(os.path.basename(center_image_path))[0]
    source_folder_name = os.path.basename(os.path.normpath(input_folder))
    output_folder = os.path.join(os.path.dirname(center_image_path), f"{base_filename}_{source_folder_name}_tween")
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    return output_folder


def load_and_resize_images(input_folder, resize_width):
    input_files = sorted([f for f in os.listdir(input_folder) if os.path.isfile(os.path.join(input_folder, f))])
    input_images = [Image.open(os.path.join(input_folder, f)) for f in input_files]
    resized_images = [resize_image(img, resize_width) for img in input_images]
    return resized_images


def save_frames_and_tweens(center_image, resized_images, num_tween_frames, image_format, compression, repeat_frames,
                           output_folder, base_filename, source_folder_name):
    frame_index = 0
    counter = 0  # Initialize counter for unique naming
    total_files = 0
    anticipated_files = len(resized_images) * (repeat_frames * 2 + num_tween_frames * 2)

    with ProcessPoolExecutor() as executor:
        for i, current_frame in enumerate(resized_images):
            # Save the current frame multiple times
            for _ in range(repeat_frames):
                current_generated_filename = os.path.join(output_folder,
                                                          f"{base_filename}_{source_folder_name}_{frame_index:06d}_frame_{counter:06d}.{image_format}")
                save_image(current_frame, current_generated_filename, image_format, compression)
                frame_index += 1
                counter += 1  # Increment counter for each frame
                total_files += 1

            # Generate and save tween frames to the center image
            tween_filenames, counter = generate_tween_frames(current_frame, center_image, num_tween_frames, frame_index,
                                                             f"{base_filename}_{source_folder_name}", output_folder,
                                                             image_format, compression, counter)
            for tween_img, tween_filename in tween_filenames:
                save_image(tween_img, tween_filename, image_format, compression)
                frame_index += 1  # Increment frame index for each tween frame
                total_files += 1

            # Save the center image multiple times
            for _ in range(repeat_frames):
                center_filename = os.path.join(output_folder,
                                               f"{base_filename}_{source_folder_name}_{frame_index:06d}_center_{counter:06d}.{image_format}")
                save_image(center_image, center_filename, image_format, compression)
                frame_index += 1  # Increment frame index for each center image
                counter += 1  # Increment counter for each frame
                total_files += 1

            # Generate and save tween frames from the center image to the next frame
            if i + 1 < len(resized_images):
                next_frame = resized_images[i + 1]
                tween_filenames, counter = generate_tween_frames(center_image, next_frame, num_tween_frames,
                                                                 frame_index, f"{base_filename}_{source_folder_name}",
                                                                 output_folder, image_format, compression, counter)
                for tween_img, tween_filename in tween_filenames:
                    save_image(tween_img, tween_filename, image_format, compression)
                    frame_index += 1  # Increment frame index for each tween frame
                    total_files += 1

    return anticipated_files, total_files


def process_tween_images(input_folder, center_image_path, num_tween_frames, image_format, compression, resize_width,
                         repeat_frames):
    center_image = Image.open(center_image_path)
    center_image = resize_image(center_image, resize_width)
    base_filename = os.path.splitext(os.path.basename(center_image_path))[0]
    source_folder_name = os.path.basename(os.path.normpath(input_folder))

    output_folder = setup_output_folder(center_image_path, input_folder)
    resized_images = load_and_resize_images(input_folder, resize_width)

    anticipated_files, total_files = save_frames_and_tweens(center_image, resized_images, num_tween_frames,
                                                            image_format, compression, repeat_frames, output_folder,
                                                            base_filename, source_folder_name)

    print(f"Anticipated number of files: {anticipated_files}")
    print(f"Actual number of files: {total_files}")


def get_user_input():
    print("Please enter the following details:")

    input_folder = input("Enter the path to the folder containing the image sequence: ")
    while not os.path.isdir(input_folder):
        print("Invalid folder path. Please try again.")
        input_folder = input("Enter the path to the folder containing the image sequence: ")

    center_image_path = input("Enter the path to the center image: ")
    while not os.path.isfile(center_image_path):
        print("Invalid file path. Please try again.")
        center_image_path = input("Enter the path to the center image: ")

    try:
        num_tween_frames = int(input("Enter the number of tween frames to generate: "))
        while num_tween_frames <= 0:
            print("Number of tween frames must be a positive integer. Please try again.")
            num_tween_frames = int(input("Enter the number of tween frames to generate: "))
    except ValueError:
        print("Invalid input. Please enter a positive integer.")
        sys.exit(1)

    image_format = input("Enter the image format (default is png, or type webp for webp): ").lower()
    if image_format not in ['png', 'webp', '']:
        print("Invalid format. Supported formats are png and webp. Defaulting to png.")
        image_format = 'png'
    if image_format == '':
        image_format = 'png'

    compression = 1 if image_format == 'webp' else 0

    try:
        resize_width = int(input("Enter the width to resize images to (maintaining aspect ratio): "))
        while resize_width <= 0:
            print("Resize width must be a positive integer. Please try again.")
            resize_width = int(input("Enter the width to resize images to (maintaining aspect ratio): "))
    except ValueError:
        print("Invalid input. Please enter a positive integer.")
        sys.exit(1)

    try:
        repeat_frames = int(input("Enter the number of times to repeat each frame: "))
        while repeat_frames <= 0:
            print("Repeat frames must be a positive integer. Please try again.")
            repeat_frames = int(input("Enter the number of times to repeat each frame: "))
    except ValueError:
        print("Invalid input. Please enter a positive integer.")
        sys.exit(1)

    return input_folder, center_image_path, num_tween_frames, image_format, compression, resize_width, repeat_frames


def main():
    input_folder, center_image_path, num_tween_frames, image_format, compression, resize_width, repeat_frames = get_user_input()
    process_tween_images(input_folder, center_image_path, num_tween_frames, image_format, compression, resize_width,
                         repeat_frames)


if __name__ == "__main__":
    main()
