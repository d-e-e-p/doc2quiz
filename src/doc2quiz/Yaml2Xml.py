#
#
#

import csv
import sys

from .Utils import create_output_dirs, validate_input_file, check_files_in_dir
from .Qti import Qti


class Yaml2Xml:
    def __init__(self, cfg):
        self.cfg = cfg

    def convert_yaml_to_xml(self, yaml_content):
        quiz = Qti(yaml_content)
        xml_content = quiz.to_qti()
        return xml_content

    def process_yaml(self):
        with open(self.cfg.input_file_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                chapter = row['chapter']
                title = row['title']
                chapter = chapter.replace('.', 'p')
                self.convert(chapter, title)

    def convert(self, chapter, title):
        yaml_file_name = f"{self.cfg.output_dir_yaml}/ch{chapter}.yaml"
        xml_file_name = f"{self.cfg.output_dir_xml}/ch{chapter}.xml"

        # TODO: check yaml_file_name exists
        with open(yaml_file_name, 'r', encoding='utf-8') as file:
            yaml_content = file.read()
            xml_content = self.convert_yaml_to_xml(yaml_content)
            if xml_content:
                with open(xml_file_name, 'w', encoding='utf-8') as file:
                    file.write(xml_content)
                    file.write(f"\n<!-- {chapter} {title} -->\n")
                    print(f'Saved ch{chapter} to {xml_file_name}')

    def check_files(self):
        try:
            if not create_output_dirs("xml", self.cfg.output_dir_xml):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_xml}")
            if not check_files_in_dir(".yaml", self.cfg.output_dir_yaml):
                raise OSError(f"input yaml directory: {self.cfg.output_dir_yaml}")
            if not validate_input_file(".csv", self.cfg.input_file_csv):
                raise OSError(f"Invalid CSV file: {self.cfg.input_file_csv}")

        except (OSError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    def run(self):
        self.check_files()
        self.process_yaml()


def yaml_to_xml(cfg):
    print("Converting from YAML to XML...")
    engine = Yaml2Xml(cfg)
    engine.run()


if __name__ == "__main__":
    pass
