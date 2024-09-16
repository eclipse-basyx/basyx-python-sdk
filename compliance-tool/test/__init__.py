import os
import zipfile

AASX_FILES = ("test_demo_full_example_json_aasx",
              "test_demo_full_example_xml_aasx",
              "test_demo_full_example_xml_wrong_attribute_aasx",
              "test_empty_aasx")


def _zip_directory(directory_path, zip_file_path):
    """Zip a directory recursively."""
    with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname=arcname)


def generate_aasx_files():
    """Zip dirs and create test AASX files."""
    script_dir = os.path.dirname(__file__)
    for i in AASX_FILES:
        _zip_directory(os.path.join(script_dir, "files", i),
                       os.path.join(script_dir, "files", i.rstrip("_aasx") + ".aasx"))


generate_aasx_files()
