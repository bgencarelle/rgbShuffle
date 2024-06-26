import os


def rename_files_sequentially(folder_path):
    # List all files in the folder
    files = sorted([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])

    # Filter to include only PNG files
    png_files = [f for f in files if f.lower().endswith('.png')]

    # Rename files to have sequential order
    for idx, file in enumerate(png_files):
        new_filename = f"{idx:06d}.png"
        old_path = os.path.join(folder_path, file)
        new_path = os.path.join(folder_path, new_filename)
        os.rename(old_path, new_path)
        print(f"Renamed {file} to {new_filename}")


def get_folder_input():
    folder_path = input("Enter the path to the folder containing the PNG files: ")
    while not os.path.isdir(folder_path):
        print("Invalid folder path. Please try again.")
        folder_path = input("Enter the path to the folder containing the PNG files: ")
    return folder_path


def main():
    folder_path = get_folder_input()
    rename_files_sequentially(folder_path)


if __name__ == "__main__":
    main()
