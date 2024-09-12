#
# Shared utils
#

import os
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class Config(BaseSettings):
    # conversion
    from_format: Literal["pdf", "txt", "yaml", "xml", ] = Field(default="pdf", alias="from")
    to_format: Literal["pdf", "txt", "yaml", "xml", "quiz"] = Field(default="txt", alias="to")
    # vars
    num_words_per_question: int = Field(default=100, alias='num_words')
    # paths

    # File paths
    input_file_pdf: str = "inputs/pdf/book.pdf"
    input_file_csv: str = "inputs/csv/toc.csv"

    # Output directories
    output_dir_pdf: str = "outputs/pdf"
    output_dir_txt: str = "outputs/txt"
    output_dir_yaml: str = "outputs/yaml"
    output_dir_xml: str = "outputs/xml"

    platform: str = "openai"
    model: str = "chatgpt-4o-latest"


def create_output_dirs(description, dirname):
    try:
        # Attempt to create the directory, including all intermediate directories
        os.makedirs(dirname, exist_ok=True)
        print(f"Directory for {description} created: '{dirname}'")
    except OSError as e:
        print(f"Error: Could not create directory for {description}: '{dirname}'. {e}")
        return False
    return True

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
