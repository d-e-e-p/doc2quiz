#
#
#
import argparse
import logging
from .Utils import Config
from .Utils import Utils

# steps
from .Pdf2Txt import pdf_to_txt         # noqa: F401
from .Txt2Yaml import txt_to_yaml       # noqa: F401
from .Yaml2Xml import yaml_to_xml       # noqa: F401
from .Xml2Quiz import xml_to_quiz       # noqa: F401

log = logging.getLogger()


class Doc2Quiz:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Convert documents into quiz format.")
        self.stages = "pdf txt yaml xml quiz".split()  # Define valid stages
        self.platforms = """ai21 anthropic aws cohere community databricks fireworks
        google-genai google-vertexai groq huggingface mistralai nvidia-ai-endpoints ollama
        openai together upstage""".split()
        self.cfg = Config()
        self.setup_args()

    def setup_args(self):
        # Use choices parameter to restrict the input and output formats to valid options
        self.parser.add_argument('--from', choices=self.stages, default="pdf",
                                 help="Specify the input format.")
        self.parser.add_argument('--to', choices=self.stages, default="txt",
                                 help="Specify the output format.")
        self.parser.add_argument('--platform', choices=self.platforms,
                                 default='openai',
                                 help="chat platform.")
        self.parser.add_argument('--model',
                                 default='gpt-4o-2024-08-06',
                                 help="chat model, eg gpt-4o-mini or claude-3-5-sonnet-20240620.")
        self.parser.add_argument('--no_feedback_images', action='store_true',
                                 help="do not generate images of pdf for feedback on quiz questions")
        self.parser.add_argument('--num_words_per_question',
                                 default='200',
                                 help="determine th number of questions for a chapter based on this ratio")

        self.parser.add_argument('--input_file_pdf',
                                 default="inputs/pdf/book.pdf",
                                 help="starting point input pdf")

        self.parser.add_argument('--input_file_csv',
                                 default="inputs/csv/toc.csv",
                                 help="starting point csv with table of contents")

    def call_method_if_exists(self, method_name):
        if method_name in globals() and callable(globals()[method_name]):
            method = globals()[method_name]
            method(self.cfg)
        else:
            log.error(f"The method '{method_name}' does not exist or is not callable.")

    def process_conversion(self):
        from_format = self.cfg.from_format
        to_format = self.cfg.to_format
        try:
            # Find indices for the conversion stages
            from_idx = self.stages.index(from_format)
            to_idx = self.stages.index(to_format)

            if from_idx >= to_idx:
                log.error(f"Conversion from {from_format} to {to_format} is not valid.")
                return

            # Loop through the required stages and call the corresponding methods
            for i in range(from_idx, to_idx):
                method_name = f"{self.stages[i]}_to_{self.stages[i + 1]}"
                Utils.change_log_file(f"logs/{method_name}.log")
                self.call_method_if_exists(method_name)

        except ValueError as e:
            log.error(f"Invalid format specified: {e}")

    def update_config(self, args):
        # from is a reserved keyword in python, so we have to use getattr
        self.cfg.from_format = getattr(args, "from")
        self.cfg.to_format = args.to
        self.cfg.platform = args.platform
        self.cfg.model = args.model
        self.cfg.no_feedback_images = args.no_feedback_images
        self.cfg.num_words_per_question = int(args.num_words_per_question)

        self.cfg.input_file_pdf = args.input_file_pdf
        self.cfg.input_file_csv = args.input_file_csv

    def run(self):
        # Parse the arguments
        args = self.parser.parse_args()
        self.update_config(args)
        self.process_conversion()


def run():
    Utils.setup_logging()
    doc2quiz = Doc2Quiz()
    doc2quiz.run()


if __name__ == "__main__":
    run()
