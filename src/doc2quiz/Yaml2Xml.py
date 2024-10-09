#
#
#

import sys
import logging

from .Utils import Utils
from .Qti import Qti

log = logging.getLogger()


class Yaml2Xml:
    def __init__(self, cfg):
        self.cfg = cfg

    def convert_yaml_to_xml(self, start_page, end_page, chapter, yaml_content):
        qti = Qti(self.cfg, start_page, end_page, chapter, yaml_content)
        qti.generate_feedback_images()
        xml_content = qti.to_xml()
        return xml_content

    def process_yaml(self):
        lines = Utils.read_toc_csv(self.cfg.input_file_csv)
        for line in lines:
            self.convert(line)

    def convert(self, line):
        start_page, end_page, chapter, title = line

        yaml_file_name = f"{self.cfg.output_dir_yaml}/{chapter}.yaml"
        xml_file_name = f"{self.cfg.output_dir_xml}/{chapter}.xml"

        # TODO: check yaml_file_name exists
        with open(yaml_file_name, 'r', encoding='utf-8') as file:
            yaml_content = file.read()
            xml_content = self.convert_yaml_to_xml(start_page, end_page, chapter, yaml_content)
            if xml_content:
                with open(xml_file_name, 'w', encoding='utf-8') as file:
                    file.write(xml_content)
                    file.write(f"\n<!-- {chapter} {title} -->\n")
                    log.info(f'Saved {chapter} to {xml_file_name}')

    def check_files(self):
        try:
            if not Utils.create_output_dirs("xml", self.cfg.output_dir_xml):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_xml}")
            if not Utils.create_output_dirs("pdf", self.cfg.output_dir_pdf):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_pdf}")
            if not self.cfg.no_feedback_images:
                if not Utils.create_output_dirs("png", self.cfg.output_dir_png):
                    raise OSError(f"Failed to create output directory: {self.cfg.output_dir_png}")

            if not Utils.check_files_in_dir(".yaml", self.cfg.output_dir_yaml):
                raise OSError(f"input yaml directory: {self.cfg.output_dir_yaml}")
            if not Utils.validate_input_file(".csv", self.cfg.input_file_csv):
                raise OSError(f"Invalid CSV file: {self.cfg.input_file_csv}")

        except (OSError) as e:
            log.error(f"Error: {e}")
            sys.exit(1)

    def run(self):
        Utils.setup_logging()
        self.check_files()
        self.process_yaml()


def yaml_to_xml(cfg):
    log.info("Converting from YAML to XML...")
    engine = Yaml2Xml(cfg)
    engine.run()


if __name__ == "__main__":
    pass
