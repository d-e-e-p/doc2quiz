#
#
#
import sys
import yaml
import json
import logging
import backoff

from .Utils import Utils
from .ExampleYaml import example_yaml
from .Quiz import Quiz
from .Search import Search

import openai
# import anthropic
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as

log = logging.getLogger()
errors = (openai.RateLimitError)


class Txt2Yaml:
    def __init__(self, cfg):
        self.cfg = cfg
        self.example_json = self.gen_example_json()
        self.search = None

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

    def get_seed_question_prompt(self, text):

        seed_q_file = "inputs/txt/ch09p0.txt"
        with open(seed_q_file, 'r', encoding='utf-8') as file:
            seed_questions = file.read()

        return f"""
You are to convert 50 questions about a passage into structured format.
The questions can be of a mixture of the following types:

    matching
    multiple_answers
    multiple_choice
    multiple_dropdowns
    short_answer
    true_false

short_answer_question should have a single word answer, with a list of potential correct answers
each answer should be marked with points from 1 to 4 to indicate difficulty of question.

quotes are extracts from the passage that best explain the answer.
the actual text of the quote is in the text field of eack quote
there must be at least one quote associated with the question.

An example of output showing different question types:

{self.example_json}

Convert all 50 questions. The 50 questions to convert are:

{seed_questions}

the passage starts here ->

{text}

<- end of passage.
"""

    def get_additional_seed_prompt(self, text, res):

        quiz = res['parsed']
        num_questions = len(quiz.questions.items)

        prompt = f"""
only {num_questions} questions were converted

please try generating questions again, but this time convert all 50 questions
        """
        return prompt

    def get_initial_prompt(self, text):
        num_words = len(text.split())
        num_questions = round(num_words / self.cfg.num_words_per_question)
        num_questions = 10

        if num_questions < 2:
            if len(text) < 100:
                log.debug(f"skiping becase text is too short len={len(text)} so num_questions={num_questions} text={text}")
                return None
            else:
                num_questions = 1
        
        return f"""
You are to produce {num_questions} questions from a passage.
The questions should be of a mixture of the following types:

    matching
    multiple_answers
    multiple_choice
    multiple_dropdowns
    short_answer
    true_false

short_answer_question should have a single word answer, with a list of potential correct answers
each answer should be marked with points from 1 to 4 to indicate difficulty of question.

quotes are extracts from the passage that best explain the answer.
the actual text of the quote is in the text field of eack quote
there must be at least one quote associated with the question.

An example of output showing different question types:

{self.example_json}

{num_questions} questions fron passage that starts here ->

{text}

<- end of passage.
"""

    def make_quotes_exact(self, quiz):
        for item in quiz["questions"]["items"]:
            log.debug(f" prompt: {item['prompt']}")
            exact_quotes = []
            for quote in item["quotes"]:
                log.debug(f" before: {quote}")
                exact_quotes.append(self.search.find_quote_in_passage(quote, ""))
                log.debug(f" after:  {quote}")
            item["quotes"] = exact_quotes
        return quiz

    def get_additional_prompt(self, text, res):

        prompt = """
the quote should be a segment of passage that explains the answers.
"""
        quiz = res['parsed']
        for item in quiz.questions.items:
            log.debug(f" prompt: {item.prompt}")
            for quote in item.quotes:
                prompt += f" quote:  {quote}"
                prompt += f" quote_text  {text[quote.start_ptr:quote.end_ptr]}\n"

        prompt += """
please try generating questions again with correct quote markers
        """
        log.debug(f" try2 prompt = {prompt}")
        return prompt

    # Define the function with backoff on rate limit errors
    @backoff.on_exception(backoff.expo, errors, base=10, factor=2, max_tries=8)
    def get_structured_llm_res(self, structured_llm, prompt):
        try:
            return structured_llm.invoke(prompt)
        except errors as e:
            log.warn(f"Rate limit hit: {e}")
            raise  # Reraise exception for backoff to handle

    def ask_questions_yaml(self, chapter, title, extracted_text):

        self.search = Search(self.cfg)

        prompt = self.get_initial_prompt(extracted_text)
        # prompt = self.get_seed_question_prompt(extracted_text)
        model = ChatOpenAI(model=self.cfg.model, temperature=0)
        structured_llm = model.with_structured_output(Quiz, include_raw=True)
        res = self.get_structured_llm_res(structured_llm, prompt)
        if res['parsing_error'] is None:
            if False:
                prompt += f"Your response was {res}"
                prompt += self.get_additional_seed_prompt(extracted_text, res)
                res = self.get_structured_llm_res(structured_llm, prompt)

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

            if 'questions' not in out_parsed:
                if not isinstance(out_parsed['questions'], dict):
                    print(f"The 'questions' key is missing in {out_parsed}")
                    return None
            # fix quotes
            # out_exact = self.make_quotes_exact(out_parsed)

            # ident has to be unique for all quiz in upload set
            title_yaml = f"{chapter} : {title}"
            ident_yaml = f"{chapter}-{self.cfg.platform}-{self.cfg.model}"
            out_edited = {'questions': {'title': title_yaml, 'ident': ident_yaml}}
            out_edited['questions'].update(out_parsed['questions'])
            yaml_str = yaml.dump(out_edited, sort_keys=False)
            return yaml_str

        else:
            print(f"parsing_error: res={res}")
            return None

    def process_csv(self):
        lines = Utils.read_toc_csv(self.cfg.input_file_csv)
        for start_page, end_page, chapter, title in lines:
            self.convert(chapter, title)

    def convert(self, chapter, title):
        txt_file_name = f"{self.cfg.output_dir_txt}/{chapter}.txt"
        yaml_file_name = f"{self.cfg.output_dir_yaml}/{chapter}.yaml"

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
                    log.info(f'Saved {chapter} to {yaml_file_name}')

    def check_files(self):
        try:
            if not Utils.create_output_dirs("yaml", self.cfg.output_dir_yaml):
                raise OSError(f"Failed to create output directory: {self.cfg.output_dir_yaml}")
            if not Utils.check_files_in_dir(".txt", self.cfg.output_dir_txt):
                raise OSError(f"input txt directory: {self.cfg.output_dir_txt}")
            if not Utils.validate_input_file(".csv", self.cfg.input_file_csv):
                raise OSError(f"Invalid CSV file: {self.cfg.input_file_csv}")

        except (OSError) as e:
            log.error(f"Error: {e}")
            sys.exit(1)

    def run(self):
        self.check_files()
        self.process_csv()


def txt_to_yaml(cfg):
    log.info("Converting from TXT to YAML...")
    engine = Txt2Yaml(cfg)
    engine.run()


if __name__ == "__main__":
    pass
