#
#
#
import argparse
from .Utils import Settings

# steps
from .Pdf2Txt import pdf_to_txt
from .Txt2Yaml import txt_to_yaml
from .Yaml2Xml import yaml_to_xml
from .Xml2Quiz import xml_to_quiz

class Doc2Quiz:
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Convert documents into quiz format.")
        self.stages = "pdf txt yaml xml quiz".split()  # Define valid stages
        self.platforms = """ai21 anthropic aws cohere community databricks fireworks
        google-genai google-vertexai groq huggingface mistralai nvidia-ai-endpoints ollama
        openai together upstage""".split()
        self.model = "gpt-4o-mini"
        self.settings = Settings()
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
        self.parser.add_argument('--model', choices=self.platforms, 
                                 help="chat model, eg gpt-4o-mini or claude-3-5-sonnet-20240620.")

    def pdf_to_txt(self):
        print("Converting from PDF to TXT...")
        pdf_to_txt(self.settings)
        pass

    def txt_to_yaml(self):
        print("Converting from TXT to YAML...")
        pass

    def yaml_to_xml(self):
        print("Converting from YAML to XML...")
        pass

    def xml_to_quiz(self):
        print("Converting from XML to Quiz format...")
        pass

    def call_method_if_exists(self, method_name):
        if method_name in globals() and callable(globals()[method_name]):
            method = globals()[method_name]
            method(self.settings)
        else:
            print(f"The method '{method_name}' does not exist or is not callable.")

    def process_conversion(self):
        from_format = self.settings.from_format
        to_format = self.settings.to_format
        try:
            # Find indices for the conversion stages
            from_idx = self.stages.index(from_format)
            to_idx = self.stages.index(to_format)

            if from_idx >= to_idx:
                print(f"Conversion from {from_format} to {to_format} is not valid.")
                print(settings)
                return

            # Loop through the required stages and call the corresponding methods
            for i in range(from_idx, to_idx):
                method_name = f"{self.stages[i]}_to_{self.stages[i+1]}"
                self.call_method_if_exists(method_name)

        except ValueError as e:
            print(f"Invalid format specified: {e}")

    def update_settings(self, args):
        # from is a reserved keyword in python
        self.settings.from_format = getattr(args, "from")
        self.settings.to_format = getattr(args, "to")
        self.settings.platform = getattr(args, "platform")
        self.settings.model = getattr(args, "model")

    def run(self):
        # Parse the arguments
        args = self.parser.parse_args()
        self.update_settings(args)
        self.process_conversion()


def run():
    doc2quiz = Doc2Quiz()
    doc2quiz.run()


if __name__ == "__main__":
    run()
