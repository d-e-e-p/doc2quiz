#
#
#
import sys
from pypdf import PdfReader
from .Utils import Utils


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

    def print_summary_table(self):
        pass

    def extract_chapter_text_from_pdf(self):
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
                    print(f'Saved from p{start_page + 1} to p{end_page + 1} to {file_name}')
        except Exception as e:
            raise PdfExtractionError(f"Error extracting chapter text from PDF: {str(e)}")

    def run(self):
        try:
            if not self.valid_inputs():
                raise InputFileError("Invalid input files.")
            if not Utils.create_output_dirs("txt", self.cfg.output_dir_txt):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_txt}")
            self.extract_chapter_text_from_pdf()
            self.print_summary_table()
        except (InputFileError, PdfExtractionError, OSError) as e:
            print(f"Error: {e}")
            sys.exit(1)


def pdf_to_txt(cfg):
    print("Converting from PDF to TXT...")
    engine = Pdf2Txt(cfg)
    engine.run()


if __name__ == "__main__":
    pass
