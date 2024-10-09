#
#
#
import sys
import logger
from pypdf import PdfReader
from prettytable import PrettyTable

from .Utils import Utils

log = logger.getLogger()


# Custom error types
class InputFileError(Exception):
    pass


class PdfExtractionError(Exception):
    pass


class Pdf2Txt:
    def __init__(self, cfg):
        self.cfg = cfg

    def valid_inputs(self):
        if not Utils.validate_input_file(".pdf", self.cfg.input_file_pdf):
            raise InputFileError(f"Invalid PDF file: {self.cfg.input_file_pdf}")
        if not Utils.validate_input_file(".csv", self.cfg.input_file_csv):
            raise InputFileError(f"Invalid CSV file: {self.cfg.input_file_csv}")
        return True

    def print_summary_table(self, res):
        table = PrettyTable()
        table.field_names = ["Chapter", "Pages", "Questions", "Title"]
        table.align["Pages"] = "r"
        table.align["Questions"] = "r"
        table.align["Title"] = "l"
        for row in res:
            table.add_row(row)

        log.info(f" number of words per question is {self.cfg.num_words_per_question}")
        log.info(table)

    def extract_chapter_text_from_pdf(self):
        res = []
        try:
            # Open the PDF file
            with open(self.cfg.input_file_pdf, 'rb') as pdf_file:
                pdf_reader = PdfReader(pdf_file)
                
                lines = Utils.read_toc_csv(self.cfg.input_file_csv)
                for start_page, end_page, chapter, title in lines:
                    # Extract text from the specified page range
                    extracted_text = ''
                    for page_num in range(start_page, end_page + 1):
                        page = pdf_reader.get_page(page_num)
                        extracted_text += page.extract_text()

                    # Save the extracted text to a file
                    file_name = f'{self.cfg.output_dir_txt}/{chapter}.txt'
                    with open(file_name, 'w', encoding='utf-8') as text_file:
                        text_file.write(f"{chapter} - {title} (pages {start_page + 1} to {end_page + 1})\n")
                        text_file.write(extracted_text)
                    log.info(f'Saved from p{start_page + 1} to p{end_page + 1} to {file_name}')
                    num_pages = end_page - start_page + 1
                    num_words = len(extracted_text.split())
                    num_questions = round(num_words / self.cfg.num_words_per_question)
                    res.append([chapter, num_pages, num_questions, title])
        except Exception as e:
            raise PdfExtractionError(f"Error extracting chapter text from PDF: {str(e)}")
        return res

    def run(self):
        try:
            if not self.valid_inputs():
                raise InputFileError("Invalid input files.")
            if not Utils.create_output_dirs("txt", self.cfg.output_dir_txt):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_txt}")
            res = self.extract_chapter_text_from_pdf()
            self.print_summary_table(res)
        except (InputFileError, PdfExtractionError, OSError) as e:
            log.error(f"Error: {e}")
            sys.exit(1)


def pdf_to_txt(cfg):
    log.info("Converting from PDF to TXT...")
    engine = Pdf2Txt(cfg)
    engine.run()


if __name__ == "__main__":
    pass
