#
#
#
import sys
import os
import zipfile
from pathlib import Path
from .CanvasInterface import upload_canvas_quiz, upload_canvas_images, upload_canvas_zipfiles
from .Utils import Utils


class Xml2Quiz:
    def __init__(self, cfg):
        self.cfg = cfg

    def process_qti_and_images(self):
        lines = Utils.read_toc_csv(self.cfg.input_file_csv)

        if not self.cfg.no_feedback_images:
            # create separate zip files for each chapter
            files_to_upload = []
            for start_page, end_page, chapter, title in lines:
                png_dirname = str(Path(self.cfg.output_dir_png, chapter))
                if os.path.isdir(png_dirname):
                    png_zipfile = str(Path(self.cfg.output_dir_zip, f"{chapter}_png.zip"))
                    parent_dir = os.path.dirname(self.cfg.output_dir_png)
                    self.zip_dir(parent_dir, png_dirname, png_zipfile)
                    files_to_upload.append(png_zipfile)

            for file in files_to_upload:
                upload_canvas_zipfiles(file)

        files_to_upload = []
        for start_page, end_page, chapter, title in lines:
            xml_filename = str(Path(self.cfg.output_dir_xml, f"{chapter}.xml"))
            if os.path.isfile(xml_filename):
                files_to_upload.append(xml_filename)

        if files_to_upload:
            qti_file_path = str(Path(self.cfg.output_dir_zip, "xml.zip"))
            parent_dir = os.path.dirname(self.cfg.output_dir_zip)
            self.zip_files(parent_dir, files_to_upload, qti_file_path)
            upload_canvas_quiz(qti_file_path)

    # Zip the xml files
    def zip_files(self, parent, file_paths, output_filename):
        if not output_filename.endswith('.zip'):
            output_filename += '.zip'
        try:
            with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in file_paths:
                    if os.path.exists(file):
                        zipf.write(file, os.path.relpath(file_path, parent))
                    else:
                        print(f"Warning: File not found: {file}")
            print(f"Zip file created successfully: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"An error occurred while creating the zip file: {str(e)}")
            return None

    def zip_dir(self, parent, dir_path, output_filename):
        if not output_filename.endswith('.zip'):
            output_filename += '.zip'

        if not os.path.isdir(dir_path):
            print(f"Error: The directory {dir_path} does not exist.")
            return None
        try:
            with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(dir_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # Write the file to the zip file with a relative path
                        zipf.write(file_path, os.path.relpath(file_path, parent))
            print(f"Zip file created successfully: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"An error occurred while creating the zip file: {str(e)}")
            return None

    def check_files(self):
        try:
            if not Utils.create_output_dirs("zip", self.cfg.output_dir_zip):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_zip}")
            if not Utils.check_files_in_dir(".xml", self.cfg.output_dir_xml):
                raise OSError(f"output xml directory: {self.cfg.output_dir_xml}")
        except (OSError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    def run(self):
        self.check_files()
        self.process_qti_and_images()


def xml_to_quiz(cfg):
    print("Converting from XML to Quiz")
    engine = Xml2Quiz(cfg)
    engine.run()


if __name__ == "__main__":
    pass
