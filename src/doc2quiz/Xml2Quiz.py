#
#
#
import sys
import os
import zipfile
from .CanvasInterface import upload_canvas_quiz, upload_canvas_images
from .Utils import Utils


class Xml2Quiz:
    def __init__(self, cfg):
        self.cfg = cfg

    def process_qti(self):
        if not self.cfg.no_feedback_images:
            upload_canvas_images(self.cfg.output_dir_png, "png")
        qti_file_path = "outputs/xml.zip"
        self.zip_dir(self.cfg.output_dir_xml, qti_file_path)
        upload_canvas_quiz(qti_file_path)
            
    # Zip the xml files
    def zip_files(self, file_paths, output_filename):
        if not output_filename.endswith('.zip'):
            output_filename += '.zip'
        try:
            with zipfile.ZipFile(output_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file in file_paths:
                    if os.path.exists(file):
                        zipf.write(file, os.path.basename(file))
                    else:
                        print(f"Warning: File not found: {file}")
            print(f"Zip file created successfully: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"An error occurred while creating the zip file: {str(e)}")
            return None

    def zip_dir(self, dir_path, output_filename):
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
                        zipf.write(file_path, os.path.relpath(file_path, dir_path))
            print(f"Zip file created successfully: {output_filename}")
            return output_filename
        except Exception as e:
            print(f"An error occurred while creating the zip file: {str(e)}")
            return None

    def check_files(self):
        try:
            if not Utils.check_files_in_dir(".xml", self.cfg.output_dir_xml):
                raise OSError(f"output xml directory: {self.cfg.output_dir_xml}")
        except (OSError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    def run(self):
        self.check_files()
        self.process_qti()


def xml_to_quiz(cfg):
    print("Converting from XML to Quiz")
    engine = Xml2Quiz(cfg)
    engine.run()


if __name__ == "__main__":
    pass
