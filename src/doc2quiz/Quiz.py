#!/usr/bin/env python3.10
from pydantic.dataclasses import dataclass
from pydantic import BaseModel, field_validator, ValidationError
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

from typing import List, Optional

class Pair(BaseModel):
    key: str
    value: str
    explanation: str

class Option(BaseModel):
    option: str
    explanation: str
    answer: bool = False

class DropdownOption(BaseModel):
    option: str
    explanation: str
    answer: bool = False

class Dropdown(BaseModel):
    dropdown: str
    options: List[DropdownOption]


class Item(BaseModel):
    type: str
    title: str
    prompt: str
    points: int
    pairs: Optional[List[Pair]] = None
    options: Optional[List[Option]] = None
    dropdowns: Optional[List[Dropdown]] = None
    answers: Optional[List[str]] = None
    answer: Optional[bool] = None
    explanation: str
    quotes: List[str]

    @field_validator('pairs', mode='before')
    def check_pairs(cls, v, info):
        if info.data['type'] == 'matching' and (v is None or len(v) == 0):
            raise ValueError('matching items must have non-empty pairs')
        if info.data['type'] != 'matching' and v is not None:
            raise ValueError(f'{info.data["type"]} items should not have pairs')
        return v

    @field_validator('options', mode='before')
    def check_options(cls, v, info):
        if info.data['type'] in ['multiple_choice', 'multiple_answers'] and (v is None or len(v) == 0):
            raise ValueError(f'{info.data["type"]} items must have non-empty options')
        if info.data['type'] not in ['multiple_choice', 'multiple_answers'] and v is not None:
            raise ValueError(f'{info.data["type"]} items should not have options')
        return v

    @field_validator('dropdowns', mode='before')
    def check_dropdowns(cls, v, info):
        if info.data['type'] == 'multiple_dropdowns' and (v is None or len(v) == 0):
            raise ValueError('multiple_dropdowns items must have non-empty dropdowns')
        if info.data['type'] != 'multiple_dropdowns' and v is not None:
            raise ValueError(f'{info.data["type"]} items should not have dropdowns')
        return v

    @field_validator('answers', mode='before')
    def check_answers(cls, v, info):
        if info.data['type'] == 'short_answer' and (v is None or len(v) == 0):
            raise ValueError('short_answer items must have non-empty answers')
        if info.data['type'] != 'short_answer' and v is not None:
            raise ValueError(f'{info.data["type"]} items should not have answers')
        return v

    @field_validator('answer', mode='before')
    def check_answer(cls, v, info):
        if info.data['type'] == 'true_false' and v is None:
            raise ValueError('true_false items must have an answer')
        if info.data['type'] != 'true_false' and v is not None:
            raise ValueError(f'{info.data["type"]} items should not have an answer')
        return v

class Questions(BaseModel):
    title: Optional[str] = None
    ident: Optional[str] = None
    items: List[Item]

class Quiz(BaseModel):
    questions: Questions

# Example usage


if __name__ == "__main__":
    with open("inputs/yaml/example.yaml", 'r', encoding='utf-8') as file:
        str = file.read()
    try:
        quiz = parse_yaml_raw_as(Quiz, str)
    except ValidationError as e:
        print(e)
    print(to_yaml_str(quiz))
    breakpoint()
