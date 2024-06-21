import os
import re
from collections import Counter


def get_numeric_part(filename):
    match = re.search(r'(\d+)', filename)
    return int(match.group(1)) if match else None


def remove_common_elements(filenames):
    split_filenames = [re.split(r'(\d+)', f) for f in filenames]
    common_prefix = os.path.commonprefix(split_filenames)
    common_suffix = os.path.commonprefix([list(reversed(f)) for f in filenames])
    common_suffix = ''.join(reversed(common_suffix))

    cleaned_filenames = []
    for parts in split_filenames:
        cleaned_filename = ''.join(part for part in parts if part not in common_prefix and part not in common_suffix)
        cleaned_filenames.append(cleaned_filename)

    return cleaned_filenames


def find_missing_files(folder_path):
    files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    cleaned_filenames = remove_common_elements(files)
    numeric_parts = [get_numeric_part(f) for f in cleaned_filenames if get_numeric_part(f) is not None]

    if not numeric_parts:
        print("No numeric parts found in filenames.")
        return []

    numeric_parts = sorted(numeric_parts)
    missing_files = []

    for num in range(numeric_parts[0], numeric_parts[-1] + 1):
        if num not in numeric_parts:
            missing_files.append(num)

    return missing_files


def write_missing_files_to_text(missing_files, output_path):
    with open(output_path, 'w') as f:
        for num in missing_files:
            f.write(f"{num:06d}\n")


def main():
    print("Please enter the following details:")

    folder_path = input("Enter the path to the folder containing the image sequence: ")
    while not os.path.isdir(folder_path):
        print("Invalid folder path. Please try again.")
        folder_path = input("Enter the path to the folder containing the image sequence: ")

    source_folder_name = os.path.basename(os.path.normpath(folder_path))
    output_file = os.path.join(folder_path, f"{source_folder_name}.txt")

    missing_files = find_missing_files(folder_path)

    if missing_files:
        write_missing_files_to_text(missing_files, output_file)
        print(f"Missing files have been listed in {output_file}.")
    else:
        print("No missing files found in the sequence.")


if __name__ == "__main__":
    main()
