#
# Shared utils
#

import os
import logging
import csv
from pydantic import Field
from pydantic_settings import BaseSettings
from typing import Literal
from colorama import Fore, Style

log = logging.getLogger()


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
    output_dir_zip: str = "outputs/zip"

    platform: str = Field(default="openai")
    model: str = Field(default="undefined")


class Utils():

    @staticmethod
    def setup_logging(log_file="logs/doc2quiz.log", file_level=logging.DEBUG, console_level=logging.INFO):
        """
        Set up logging with colored console output and plain file output.

        Args:
            log_file (str): Path to the log file.
            file_level (int): Logging level for the file handler.
            console_level (int): Logging level for the console handler.
        """
        # Ensure the log directory exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w'):
            pass  # This empties the file

        # Get the top-level logger
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)  # Set the minimum log level for the logger

        # Create a file handler for logging to a file
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        
        # Create a console (stream) handler for logging to the screen
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)

        # Define a common format for both handlers
        plain_formatter = logging.Formatter(' %(levelname)s - %(funcName)s - %(message)s')
        file_handler.setFormatter(plain_formatter)  # Plain format for file logs
        
        # Custom formatter for console with colors
        class ColorFormatter(logging.Formatter):
            def format(self, record):
                level_color = {
                    logging.DEBUG: Fore.BLUE,
                    logging.INFO: Fore.GREEN,
                    logging.WARNING: Fore.YELLOW,
                    logging.ERROR: Fore.RED,
                    logging.CRITICAL: Fore.MAGENTA + Style.BRIGHT
                }.get(record.levelno, Fore.WHITE)

                # Color for funcName
                func_color = Fore.MAGENTA  # Purple for function name

                # Add color to the level name and function name
                record.levelname = f"{level_color}{record.levelname}{Style.RESET_ALL}"
                record.funcName = f"{func_color}{record.funcName}{Style.RESET_ALL}"

                return super().format(record)

        color_formatter = ColorFormatter(' %(levelname)s - %(funcName)s - %(message)s')
        console_handler.setFormatter(color_formatter)  # Colored format for console logs

        # Add both handlers to the logger if not already added
        if not log.handlers:
            log.addHandler(file_handler)
            log.addHandler(console_handler)

        # Save the file handler to logger for reference
        log.file_handler = file_handler
        return log

    @staticmethod
    def change_log_file(log_file):
        """
        Change the log file during runtime by replacing the existing file handler.

        Args:
            log_file (str): Path to the new log file.
        """
        
        # Ensure the directory for the new log file exists
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        with open(log_file, 'w'):
            pass  # This empties the file

        # Remove existing file handler, if it exists
        if hasattr(log, "file_handler"):
            log.removeHandler(log.file_handler)

        # Create a new file handler with the new file path
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(' %(levelname)s - %(message)s'))

        # Add the new file handler to the logger
        log.addHandler(file_handler)
        
        # Update the reference to the new file handler
        log.file_handler = file_handler

    @staticmethod
    def set_logging_level(level=logging.INFO):
        for handler in log.handlers:
            handler.setLevel(level)

    @staticmethod
    def create_output_dirs(description, dirname):
        try:
            # Attempt to create the directory, including all intermediate directories
            os.makedirs(dirname, exist_ok=True)
            log.info(f"Directory for {description} created: '{dirname}'")
        except OSError as e:
            log.error(f"Error: Could not create directory for {description}: '{dirname}'. {e}")
            return False
        return True

    @staticmethod
    def validate_input_file(description, filename):

        if os.path.isfile(filename):
            if filename.endswith(description):
                return True
            else:
                log.info(f" Expecting file {filename} to be a {description} file")
                return False
        else:
            log.warn(f" {description} file {filename} does not exist")
            return False

    @staticmethod
    def check_files_in_dir(suffix, dirname):
        # Check if the directory exists
        if not os.path.isdir(dirname):
            log.warn(f"Directory does not exist: {dirname}")
            return False

        # Check for files with suffix in the directory
        txt_files = [f for f in os.listdir(dirname) if f.endswith(suffix)]

        if txt_files:
            return True
        else:
            log.warn(f"No {suffix} files found in {dirname}")
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
