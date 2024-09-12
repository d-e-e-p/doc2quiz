#
#
#
import sys
import os
import yaml
import csv
import json

from .Utils import create_output_dirs, validate_input_file, check_files_in_dir
from .ExampleYaml import example_yaml
from .Quiz import Quiz

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, field_validator, ValidationError
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str


class Txt2Yaml:
    def __init__(self, cfg):
        self.cfg = cfg
        self.example_json = self.gen_example_json()

    def gen_example_json(self):
        quiz_parsed = parse_yaml_raw_as(Quiz, example_yaml)
        quiz_cleaned = self.remove_optional_nulls(quiz_parsed)
        json_str = json.dumps(quiz_cleaned)
        return json_str

    def remove_optional_nulls(self, obj):
        if isinstance(obj, BaseModel):
            cleaned_data = {}
            for key, value in obj.dict(exclude_none=True).items():
                cleaned_data[key] = self.remove_optional_nulls(value)
            return cleaned_data
        elif isinstance(obj, list):
            return [self.remove_optional_nulls(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self.remove_optional_nulls(value) for key, value in obj.items() if value is not None}
        else:
            return obj

    def get_prompt(self, text):
        num_questions = round(len(text) / self.cfg.num_words_per_question)

        if num_questions < 2:
            if len(text) < 100:
                print(f"Skipping ch{chapter} : {title} : length len={len(text)} so num_questions={num_questions}")
                return None
            else:
                num_questions = 1
        
        return f"""
You are to produce  {num_questions} questions from a passage.
The questions should be of a mixture of the following types:

    matching
    multiple_answers
    multiple_choice
    multiple_dropdowns
    short_answer
    true_false

short_answer_question should have a single word answer, with a list of potential correct answers
each answer should be marked with points from 1 to 4 to indicate difficulty of question.
quote is an excerpt from passage explaining the answer to the question. the quote should be exact
including spaces and punctuation.

An example of output showing different question types:

{self.example_json}

the passage:

{text}

end of passage.
"""
    
    def ask_questions_yaml(self, chapter, title, extracted_text):

        prompt = self.get_prompt(extracted_text)
        model = ChatOpenAI(model=self.cfg.model, temperature=0)
        structured_llm = model.with_structured_output(Quiz, include_raw=True)
        res = structured_llm.invoke(prompt)
        if res['parsing_error'] is None:
            out_parsed = self.remove_optional_nulls(res['parsed'])
            yaml_str = yaml.dump(out_parsed, sort_keys=False)
            out_from_yaml = parse_yaml_raw_as(Quiz, yaml_str)
            out_recreate = self.remove_optional_nulls(out_from_yaml)
            out_check = out_parsed == out_recreate
            if out_check:
                pass
                # print(f" out_check passed = {out_check}")
            else:
                print(f"out check mismatch: out_parsed  = \n{out_parsed}")
                print(f"out check mismatch: out_check   = \n{out_check}")
            # update with title and ident

            if 'questions' in out_parsed and isinstance(out_parsed['questions'], dict):
                title_yaml = f"ch{chapter} : {title}"
                ident_yaml = f"{self.cfg.platform}-{self.cfg.model}"
                out_edited = {'questions': {'title': title_yaml, 'ident': ident_yaml}}
                out_edited['questions'].update(out_parsed['questions'])
                yaml_str = yaml.dump(out_edited, sort_keys=False)
                return yaml_str
            else:
                print(f"The 'questions' key is missing in {out_parsed}")
                return None

        else:
            print(f"parsing_error: res={res}")
            return None

    def process_csv(self):
        with open(self.cfg.input_file_csv, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            for row in csv_reader:
                chapter = row['chapter']
                title = row['title']
                chapter = chapter.replace('.', 'p')
                self.convert(chapter, title)

    def convert(self, chapter, title):
        txt_file_name = f"{self.cfg.output_dir_txt}/ch{chapter}.txt"
        yaml_file_name = f"{self.cfg.output_dir_yaml}/ch{chapter}.yaml"

        # TODO: check txt_file_name exists
        with open(txt_file_name, 'r', encoding='utf-8') as file:
            extracted_text = file.read()

            yaml_txt = self.ask_questions_yaml(chapter, title, extracted_text)
            if yaml_txt:
                with open(yaml_file_name, 'w', encoding='utf-8') as file:
                    file.write(f"# {chapter} : {title}\n")
                    # TODO: process yaml to add additional tags
                    file.write(yaml_txt)
                    file.write("\n")
                    print(f'Saved ch{chapter} to {yaml_file_name}')

    def check_files(self):
        try:
            if not create_output_dirs("yaml", self.cfg.output_dir_yaml):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_yaml}")
            if not check_files_in_dir(".txt", self.cfg.output_dir_txt):
                raise OSError(f"input txt directory: {self.cfg.output_dir_txt}")
            if not validate_input_file(".csv", self.cfg.input_file_csv):
                raise OSError(f"Invalid CSV file: {self.cfg.input_file_csv}")

        except (OSError) as e:
            print(f"Error: {e}")
            sys.exit(1)

    def run(self):
        self.check_files()
        self.process_csv()


def txt_to_yaml(cfg):
    print("Converting from TXT to YAML...")
    engine = Txt2Yaml(cfg)
    engine.run()


if __name__ == "__main__":
    pass
