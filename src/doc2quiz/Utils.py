#
# Shared utils
#

import os
import csv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Literal


class Config(BaseSettings):
    # conversion
    from_format: Literal["pdf", "txt", "yaml", "xml", ] = Field(default="pdf", alias="from")
    to_format: Literal["pdf", "txt", "yaml", "xml", "quiz"] = Field(default="txt", alias="to")
    # vars
    num_words_per_question: int = Field(default=250, alias='num_words')
    no_feedback_images: bool = False
    # paths

    # File paths
    input_file_pdf: str = "inputs/pdf/book.pdf"
    input_file_csv: str = "inputs/csv/toc.csv"

    # Output directories
    output_dir_pdf: str = "outputs/pdf"
    output_dir_txt: str = "outputs/txt"
    output_dir_yaml: str = "outputs/yaml"
    output_dir_xml: str = "outputs/xml"
    output_dir_png: str = "outputs/png"
    output_dir_pdf: str = "outputs/pdf"

    platform: str = Field(default="openai")
    model: str = Field(default="undefined")


class Utils():

    @staticmethod
    def create_output_dirs(description, dirname):
        try:
            # Attempt to create the directory, including all intermediate directories
            os.makedirs(dirname, exist_ok=True)
            print(f"Directory for {description} created: '{dirname}'")
        except OSError as e:
            print(f"Error: Could not create directory for {description}: '{dirname}'. {e}")
            return False
        return True

    @staticmethod
    def validate_input_file(description, filename):

        if os.path.isfile(filename):
            if filename.endswith(description):
                return True
            else:
                print(f" Expecting file {filename} to be a {description} file")
                return False
        else:
            print(f" {description} file {filename} does not exist")
            return False

    @staticmethod
    def check_files_in_dir(suffix, dirname):
        # Check if the directory exists
        if not os.path.isdir(dirname):
            print(f"Directory does not exist: {dirname}")
            return False

        # Check for files with suffix in the directory
        txt_files = [f for f in os.listdir(dirname) if f.endswith(suffix)]

        if txt_files:
            return True
        else:
            print(f"No {suffix} files found in {dirname}")
            return False

    @staticmethod
    def read_toc_csv(filename):
        """
        read the table of contents and echo out the information
        """
        # headers = ['start', 'end', 'chapter', 'title']
        lines = []
        with open(filename, 'r') as csv_file:
            csv_reader = csv.reader(csv_file, skipinitialspace=True)
            # Skip the first line (header)
            next(csv_reader)
            # Iterate through each row in the CSV
            chapter_prefix = "ch"
            for row in csv_reader:
                start_page = int(row[0].strip()) - 1
                end_page = int(row[1].strip()) - 1
                # 3.1 -> ch3p1
                chapter = chapter_prefix + row[2].strip().replace('.', 'p')
                title = row[3].strip()
                lines.append([start_page, end_page, chapter, title])
        return lines
    

if __name__ == "__main__":
    lines = Utils.read_toc_csv("inputs/csv/toc_full.csv")
    breakpoint()
