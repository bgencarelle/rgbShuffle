import numpy as np
import cv2
import os
import sys


def find_neutral_point(image, grid_size=5):
    height, width, _ = image.shape
    h_step = height // grid_size
    w_step = width // grid_size

    avg_rgb_values = []

    for i in range(grid_size):
        for j in range(grid_size):
            grid = image[i * h_step:(i + 1) * h_step, j * w_step:(j + 1) * w_step, :]
            avg_rgb = np.mean(grid, axis=(0, 1))
            avg_rgb_values.append(avg_rgb)

    neutral_point = np.mean(avg_rgb_values, axis=0)
    return neutral_point


def apply_white_balance(image, scaling_factors):
    balanced_image = np.zeros_like(image, dtype=np.float32)
    for c in range(3):
        balanced_image[:, :, c] = image[:, :, c] * scaling_factors[c]
    max_val = np.iinfo(image.dtype).max if np.issubdtype(image.dtype, np.integer) else 1.0
    balanced_image = np.clip(balanced_image, 0, max_val).astype(image.dtype)
    return balanced_image


def white_balance_matrix(image, neutral_point):
    g_scale = neutral_point[1]
    scaling_factors = neutral_point / g_scale
    scaling_factors = np.clip(scaling_factors, 0, 10)
    return apply_white_balance(image, scaling_factors)


def apply_color_correction(image, correction_matrix):
    corrected_image = cv2.transform(image, correction_matrix)
    max_val = np.iinfo(image.dtype).max if np.issubdtype(image.dtype, np.integer) else 1.0
    corrected_image = np.clip(corrected_image, 0, max_val).astype(image.dtype)
    return corrected_image


def white_balance_advanced(image, neutral_point):
    if image.dtype != np.float32:
        image = image.astype(np.float32) / 65535.0 if image.dtype == np.uint16 else image.astype(np.float32) / 255.0

    correction_matrix = np.array([
        [1.1, 0.05, 0.05],
        [0.05, 1.1, 0.05],
        [0.05, 0.05, 1.1]
    ], dtype=np.float32)

    corrected_image = apply_color_correction(image, correction_matrix)

    if image.dtype == np.float32:
        corrected_image = (corrected_image * 65535).astype(np.uint16) if image.dtype == np.uint16 else (
                    corrected_image * 255).astype(np.uint8)

    return corrected_image


def process_image_file(input_image_path, output_image_path_matrix, output_image_path_ccm):
    print(f"Processing {input_image_path}...")

    image = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        print(f"Error: Unable to open/read the image file at {input_image_path}. Check the file path and integrity.")
        return

    if image.dtype == np.uint16:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0

    neutral_point = find_neutral_point(image)
    print(f"Neutral point for {input_image_path}: {neutral_point}")

    wb_image_matrix = white_balance_matrix(image, neutral_point)
    wb_image_ccm = white_balance_advanced(image, neutral_point)

    if image.dtype == np.float32:
        wb_image_matrix = (cv2.cvtColor(wb_image_matrix, cv2.COLOR_RGB2BGR) * 255).astype(np.uint8)
        wb_image_ccm = (cv2.cvtColor(wb_image_ccm, cv2.COLOR_RGB2BGR) * 255).astype(np.uint8)
    elif image.dtype == np.uint16:
        wb_image_matrix = cv2.cvtColor(wb_image_matrix, cv2.COLOR_RGB2BGR)
        wb_image_ccm = cv2.cvtColor(wb_image_ccm, cv2.COLOR_RGB2BGR)

    success_matrix = cv2.imwrite(output_image_path_matrix, wb_image_matrix)
    if success_matrix:
        print(f"Saved processed image (matrix) to {output_image_path_matrix}")
    else:
        print(f"Error: Unable to save processed image (matrix) to {output_image_path_matrix}")

    success_ccm = cv2.imwrite(output_image_path_ccm, wb_image_ccm)
    if success_ccm:
        print(f"Saved processed image (ccm) to {output_image_path_ccm}")
    else:
        print(f"Error: Unable to save processed image (ccm) to {output_image_path_ccm}")


def process_folder(input_folder_path, output_folder_base, output_format, folder_name):
    supported_extensions = ('.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp')
    files_found = False

    for root, dirs, files in os.walk(input_folder_path):
        for filename in files:
            if filename.lower().endswith(supported_extensions):
                files_found = True
                input_image_path = os.path.join(root, filename)

                # Create the corresponding output paths
                relative_path = os.path.relpath(root, input_folder_path)
                output_folder_path_matrix = os.path.join(output_folder_base, folder_name + "_wb", relative_path)
                output_folder_path_ccm = os.path.join(output_folder_base, folder_name + "_ccm", relative_path)

                if not os.path.exists(output_folder_path_matrix):
                    os.makedirs(output_folder_path_matrix)
                if not os.path.exists(output_folder_path_ccm):
                    os.makedirs(output_folder_path_ccm)

                output_image_path_matrix = os.path.join(output_folder_path_matrix,
                                                        os.path.splitext(filename)[0] + '_wb.' + output_format)
                output_image_path_ccm = os.path.join(output_folder_path_ccm,
                                                     os.path.splitext(filename)[0] + '_ccm.' + output_format)

                process_image_file(input_image_path, output_image_path_matrix, output_image_path_ccm)

    if not files_found:
        print("No supported image files found in the directory.")


def main():
    if len(sys.argv) != 3:
        print("Usage: python whiteBalance.py <path_to_folder> <output_format>")
        print("Supported output formats: png, jpg, jpeg, tiff, bmp, webp")
        return

    input_folder_path = sys.argv[1].rstrip('/')
    output_format = sys.argv[2].lower()

    supported_formats = ('png', 'jpg', 'jpeg', 'tiff', 'tif', 'bmp', 'webp')
    if output_format not in supported_formats:
        print(f"Error: The output format {output_format} is not supported.")
        return

    if not os.path.isdir(input_folder_path):
        print(f"Error: The path {input_folder_path} is not a valid directory.")
        return

    parent_dir = os.path.dirname(input_folder_path)
    folder_name = os.path.basename(input_folder_path)
    output_folder_base = os.path.join(parent_dir, folder_name + "_processed")

    process_folder(input_folder_path, output_folder_base, output_format, folder_name)


if __name__ == "__main__":
    main()
