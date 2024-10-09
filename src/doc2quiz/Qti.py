#!/usr/bin/env python3

import random
import re
import hashlib
import logging
import xml.etree.ElementTree as ET
from xml.dom import minidom


from pydantic_yaml import parse_yaml_raw_as

from .Quiz import Quiz
from .ImageGen import ImageGen

log = logging.getLogger()


class Qti:
    def __init__(self, cfg, start_page, end_page, chapter, yaml_content):
        self.generated_ids = set()
        self.cfg = cfg
        self.chapter = chapter
        self.start_page = start_page
        self.end_page = end_page
        self.quiz = self.parse_quiz_yaml(yaml_content)
        self.image_gen = ImageGen(cfg, start_page, end_page, chapter)
        self.quote_images = {}

    def parse_quiz_yaml(self, yaml_content) -> 'Quiz':
        quiz = parse_yaml_raw_as(Quiz, yaml_content)
        return quiz

    def generate_unique_id(self):
        while True:
            # Generate a random 5-digit number
            new_id = random.randint(10000, 99999)
            # Ensure the ID is unique
            if new_id not in self.generated_ids:
                self.generated_ids.add(new_id)
                return new_id

    def handle_item(self, item, item_element):
        method_name = f"_handle_{item.type}_item"
        method = getattr(self, method_name, None)
        if method:
            method(item, item_element)
        else:
            log.error(f"No handler found for item type: {item.type}")

    def hash_string_to_key(self, text, length=8):
        hash_object = hashlib.sha256(text.encode('utf-8'))
        short_hash = hash_object.hexdigest()[:length]
        return short_hash

    def generate_feedback_images(self):
        # loop over all feedback items
        # List to hold all quotes
        if self.cfg.no_feedback_images:
            return

        quotes = {}
        for item in self.quiz.questions.items:
            item.ident = f"item{self.generate_unique_id()}"
            if item.quotes:
                quotes[item.ident] = item.quotes

        self.quote_images = self.image_gen.generate(quotes, self.chapter)

    def to_xml(self) -> str:
        # Create the root element with the necessary namespaces
        questestinterop = ET.Element("questestinterop", {
            "xmlns": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.imsglobal.org/xsd/ims_qtiasiv1p2p1.xsd"
        })

        # Create the assessment element
        title = f"{self.quiz.questions.title}"
        ident = f"{self.quiz.questions.ident}"
        # assessment = ET.SubElement(questestinterop, "assessment", ident=self.quiz.ident, title=self.quiz.title)
        assessment = ET.SubElement(questestinterop, "assessment", ident=ident, title=title)

        # Metadata for the assessment
        qtimetadata = ET.SubElement(assessment, "qtimetadata")
        qtimetadatafield = ET.SubElement(qtimetadata, "qtimetadatafield")
        fieldlabel = ET.SubElement(qtimetadatafield, "fieldlabel")
        fieldlabel.text = "cc_maxattempts"
        fieldentry = ET.SubElement(qtimetadatafield, "fieldentry")
        fieldentry.text = "1"

        # Create the root section element
        # section = ET.SubElement(assessment, "section", ident="root_section")
        section = ET.SubElement(assessment, "section", ident=title)

        # Iterate over each item in the quiz
        for i, item in enumerate(self.quiz.questions.items, start=1):
            item_element = ET.SubElement(section, "item", ident=item.ident, title=item.title)

            # Item metadata
            itemmetadata = ET.SubElement(item_element, "itemmetadata")
            qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")

            qtimetadatafield = ET.SubElement(qtimetadata, "qtimetadatafield")
            fieldlabel = ET.SubElement(qtimetadatafield, "fieldlabel")
            fieldlabel.text = "question_type"
            fieldentry = ET.SubElement(qtimetadatafield, "fieldentry")
            fieldentry.text = self.get_question_type(item)

            qtimetadatafield = ET.SubElement(qtimetadata, "qtimetadatafield")
            fieldlabel = ET.SubElement(qtimetadatafield, "fieldlabel")
            fieldlabel.text = "points_possible"
            fieldentry = ET.SubElement(qtimetadatafield, "fieldentry")
            fieldentry.text = str(item.points)

            self.handle_item(item, item_element)

        # Generate the XML string
        qti_string = self.prettify(questestinterop)
        # qti_string = hack_xml(qti_string)
        return qti_string

    def safe_tostring(self, element):
        for subelement in element.iter():
            for key, value in subelement.attrib.items():
                log.debug(f" k={key} v={value}")
                if value is None:
                    log.debug(f" --------------------------------- NONE k={key} v={value}")
                    subelement.attrib[key] = ""
            if subelement.text is None:
                log.debug(f" --------------------------------- NONE k={subelement.text}")
                subelement.text = ""
        return ET.tostring(element)

    def prettify(self, element):
        rough_string = ET.tostring(element, 'utf-8')
        # rough_string = self.safe_tostring(element)
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def get_question_type(self, item) -> str:
        # Define a mapping of item classes to question type strings
        qtype = item.type + "_question"
        return qtype

    def _handle_multiple_answers_item(self, item, item_element):
        self._handle_multiple_choice_item(item, item_element)

    def _handle_multiple_choice_item(self, item, item_element):
        # Determine if it's a single-answer or multiple-answer question
        is_multiple_answers = (item.type == "multiple_answers")
        
        # Add the presentation element
        presentation = ET.SubElement(item_element, "presentation")

        # Add the prompt
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = item.prompt

        # Create response_lid element
        response_lid = ET.SubElement(presentation, "response_lid",
                                     ident="response1",
                                     rcardinality="Multiple" if is_multiple_answers else "Single")
        render_choice = ET.SubElement(response_lid, "render_choice")

        # Add options
        for i, option in enumerate(item.options, start=1):
            response_label = ET.SubElement(render_choice, "response_label", ident=f"option{i}")
            material = ET.SubElement(response_label, "material")
            mattext = ET.SubElement(material, "mattext", texttype="text/plain")
            mattext.text = str(option.option)

        # Add resprocessing element
        resprocessing = ET.SubElement(item_element, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(outcomes, "decvar", maxvalue="100", minvalue="0", varname="SCORE", vartype="Decimal")

        # Calculate points per correct answer
        num_correct_options = sum(option.answer for option in item.options)
        if num_correct_options < 1:
            breakpoint()
        points_per_correct = 100.0 / num_correct_options

        # Add conditions for correct answers
        for i, option in enumerate(item.options, start=1):
            if option.answer:
                respcondition = ET.SubElement(resprocessing, "respcondition")
                conditionvar = ET.SubElement(respcondition, "conditionvar")
                varequal = ET.SubElement(conditionvar, "varequal", respident="response1")
                varequal.text = f"option{i}"
                setvar = ET.SubElement(respcondition, "setvar", action="Add", varname="SCORE")
                setvar.text = str(points_per_correct)

                # Add feedback for this option
                # ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid=f"feedback_{i}")

        # Add general feedback (explanation)
        self._add_general_feedback(item_element, item)
                
        # Add feedback for each option
        for i, option in enumerate(item.options, start=1):
            if option.explanation:
                itemfeedback = ET.SubElement(item_element, "itemfeedback", ident=f"feedback_{i}")
                flow_mat = ET.SubElement(itemfeedback, "flow_mat")
                material = ET.SubElement(flow_mat, "material")
                mattext = ET.SubElement(material, "mattext", texttype="text/html")
                feedback_text = option.explanation
                mattext.text = feedback_text

    def extract_blanks(self, text):
        # Use regex to find all substrings inside square brackets
        pattern = r'\[([^\]]+)\]'
        matches = re.findall(pattern, text)
        return matches

    def get_ident_from_prompt(self, i, dropdown, dropdowns, prompt):
        # extract labels for response_ from prompt...
        label_blanks = self.extract_blanks(prompt)
        dropdown_blanks = [dd.dropdown for dd in dropdowns]
        are_equal = set(label_blanks) == set(dropdown_blanks)
        if not are_equal:
            log.warn(f"WARNING: blanks not equal. label_blanks = {label_blanks} dropdown_blanks={dropdown_blanks}")

        if dropdown.dropdown:
            ident = "response_" + dropdown.dropdown
        else:
            ident = "response_" + label_blanks[i]

        return ident

    def _add_general_feedback(self, item_element, item):
        if hasattr(item, 'explanation'):
            itemfeedback = ET.SubElement(item_element, "itemfeedback", ident="general_fb")
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext", texttype="text/html")
            mattext.text = item.explanation

        if hasattr(item, 'quotes') and not self.cfg.no_feedback_images:
            if item.ident in self.quote_images:
                mattext.text += "\n"
                for imgname in self.quote_images[item.ident]:
                    imgsrc = f"$IMS-CC-FILEBASE$/Uploaded Media/png/{imgname}"
                    mattext.text += f"""<img src="{imgsrc}">\n"""

    def _handle_multiple_dropdowns_item(self, item, item_element):
        # Add the presentation element
        presentation = ET.SubElement(item_element, "presentation")

        # Add the prompt
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = item.prompt

        # Create response_lid elements for each dropdown
        for i, dropdown in enumerate(item.dropdowns, start=1):
            ident = self.get_ident_from_prompt(i, dropdown, item.dropdowns, item.prompt)
                
            response_lid = ET.SubElement(presentation, "response_lid", ident=ident, rcardinality="Single")
            material = ET.SubElement(response_lid, "material")
            mattext = ET.SubElement(material, "mattext", texttype="text/plain")
            mattext.text = str(dropdown.dropdown)  # The label for this dropdown

            render_choice = ET.SubElement(response_lid, "render_choice")
            for j, option in enumerate(dropdown.options, start=1):
                response_label = ET.SubElement(render_choice, "response_label", ident=f"option_{i}_{j}")
                material = ET.SubElement(response_label, "material")
                mattext = ET.SubElement(material, "mattext", texttype="text/plain")
                mattext.text = str(option.option)

        # Add resprocessing element
        resprocessing = ET.SubElement(item_element, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(outcomes, "decvar", maxvalue="100", minvalue="0", varname="SCORE", vartype="Decimal")

        # Calculate points per dropdown
        points_per_dropdown = 100.0 / len(item.dropdowns)

        # Add conditions for each dropdown
        for i, dropdown in enumerate(item.dropdowns, start=1):
            ident = self.get_ident_from_prompt(i, dropdown, item.dropdowns, item.prompt)
            respcondition = ET.SubElement(resprocessing, "respcondition")
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal", respident=ident)
            
            # Find the correct answer for this dropdown
            for j, option in enumerate(dropdown.options, start=1):
                if option.answer:
                    ident = f"option_{i}_{j}"
                    # body of text contains the ident!
                    varequal.text = ident
                    setvar = ET.SubElement(respcondition, "setvar", action="Add", varname="SCORE")
                    setvar.text = str(points_per_dropdown)

            # Add feedback for this dropdown
            ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid=f"feedback_{i}")

        # Add general feedback (explanation)
        self._add_general_feedback(item_element, item)

        # Add feedback for each dropdown
        for i, dropdown in enumerate(item.dropdowns, start=1):
            itemfeedback = ET.SubElement(item_element, "itemfeedback", ident=f"feedback_{i}")
            flow_mat = ET.SubElement(itemfeedback, "flow_mat")
            material = ET.SubElement(flow_mat, "material")
            mattext = ET.SubElement(material, "mattext", texttype="text/html")
            
            # Find the correct answer and its explanation for this dropdown
            for j, option in enumerate(dropdown.options, start=1):
                if option.answer:
                    feedback_text = f"The correct answer for '{dropdown.dropdown}' is '{option.option}'. "
                    if option.explanation:
                        feedback_text += option.explanation
                    mattext.text = feedback_text

    def _handle_short_answer_item(self, item, item_element):
        # Add the presentation element
        presentation = ET.SubElement(item_element, "presentation")

        # Add the prompt
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = item.prompt

        # Create response_str element
        response_str = ET.SubElement(presentation, "response_str", ident="response1", rcardinality="Single")
        render_fib = ET.SubElement(response_str, "render_fib")
        ET.SubElement(render_fib, "response_label", ident="label1", rshuffle="No")

        # Add resprocessing element
        resprocessing = ET.SubElement(item_element, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(outcomes, "decvar", maxvalue="100", minvalue="0", varname="SCORE", vartype="Decimal")

        # Add condition for correct answer
        respcondition = ET.SubElement(resprocessing, "respcondition")
        respcondition.set("continue", "No")
        conditionvar = ET.SubElement(respcondition, "conditionvar")

        answers = [item.answers] if not isinstance(item.answers, list) else item.answers
        for answer in answers:
            varequal = ET.SubElement(conditionvar, "varequal", respident="response1", case="No")
            varequal.text = str(answer)
        ET.SubElement(respcondition, "setvar", action="Set", varname="SCORE").text = "100"

        # Add feedback for correct answer
        ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid="correct_fb")

        # Add feedback for incorrect answer
        ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid="incorrect_fb")

        # Add general feedback (explanation)
        self._add_general_feedback(item_element, item)

#        # Add correct feedback
#        itemfeedback = ET.SubElement(item_element, "itemfeedback", ident="correct_fb")
#        flow_mat = ET.SubElement(itemfeedback, "flow_mat")
#        material = ET.SubElement(flow_mat, "material")
#        mattext = ET.SubElement(material, "mattext", texttype="text/html")
#        mattext.text = "Correct!"
#
#        # Add incorrect feedback
#        itemfeedback = ET.SubElement(item_element, "itemfeedback", ident="incorrect_fb")
#        flow_mat = ET.SubElement(itemfeedback, "flow_mat")
#        material = ET.SubElement(flow_mat, "material")
#        mattext = ET.SubElement(material, "mattext", texttype="text/html")
#        mattext.text = "Incorrect. The correct answer is: " + item.answer

    def _handle_true_false_item(self, item, item_element):
        # Add the presentation element
        presentation = ET.SubElement(item_element, "presentation")

        # Add the prompt
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = item.prompt

        # Create response_lid element
        response_lid = ET.SubElement(presentation, "response_lid", ident="response1", rcardinality="Single")
        render_choice = ET.SubElement(response_lid, "render_choice")

        # Add True and False options
        for value, label in [("true", "True"), ("false", "False")]:
            response_label = ET.SubElement(render_choice, "response_label", ident=value)
            material = ET.SubElement(response_label, "material")
            mattext = ET.SubElement(material, "mattext", texttype="text/plain")
            mattext.text = label

        # Add resprocessing element
        resprocessing = ET.SubElement(item_element, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(outcomes, "decvar", maxvalue="100", minvalue="0", varname="SCORE", vartype="Decimal")

        # Add condition for correct answer
        respcondition = ET.SubElement(resprocessing, "respcondition")
        respcondition.set("continue", "No")  # Changed this line
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        varequal = ET.SubElement(conditionvar, "varequal", respident="response1")
        varequal.text = str(item.answer).lower()
        ET.SubElement(respcondition, "setvar", action="Set", varname="SCORE").text = "100"

        # Add feedback for correct answer
        ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid="correct_fb")

        # Add condition for incorrect answer
        respcondition = ET.SubElement(resprocessing, "respcondition")
        respcondition.set("continue", "No")  # Changed this line
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        # not_element = ET.SubElement(conditionvar, "not")
        # varequal = ET.SubElement(not_element, "varequal", respident="response1")
        varequal = ET.SubElement(conditionvar, "varequal", respident="response1")
        varequal.text = str(not item.answer).lower()
        # ET.SubElement(respcondition, "setvar", action="Set", varname="SCORE").text = "0"

        # Add feedback for incorrect answer
        ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid="incorrect_fb")

        # Add general feedback (explanation)
        self._add_general_feedback(item_element, item)

        # Add correct feedback
        itemfeedback = ET.SubElement(item_element, "itemfeedback", ident="correct_fb")
        flow_mat = ET.SubElement(itemfeedback, "flow_mat")
        material = ET.SubElement(flow_mat, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = "Correct!"

        # Add incorrect feedback
        itemfeedback = ET.SubElement(item_element, "itemfeedback", ident="incorrect_fb")
        flow_mat = ET.SubElement(itemfeedback, "flow_mat")
        material = ET.SubElement(flow_mat, "material")
        mattext = ET.SubElement(material, "mattext", texttype="text/html")
        mattext.text = "Incorrect."

    def _handle_matching_item(self, item, item_element):
        # Add the presentation element
        presentation = ET.SubElement(item_element, "presentation")
        
        # Add the prompt
        material = ET.SubElement(presentation, "material")
        mattext = ET.SubElement(material, "mattext")
        mattext.text = item.prompt
        
        # Create response_lid elements for each pair
        for i, pair in enumerate(item.pairs, start=1):
            response_lid = ET.SubElement(presentation, "response_lid", ident=f"response{i}")
            
            material = ET.SubElement(response_lid, "material")
            mattext = ET.SubElement(material, "mattext")
            mattext.text = str(pair.key)
            
            render_choice = ET.SubElement(response_lid, "render_choice")
            for j, p in enumerate(item.pairs, start=1):
                response_label = ET.SubElement(render_choice, "response_label", ident=f"label{j}")
                material = ET.SubElement(response_label, "material")
                mattext = ET.SubElement(material, "mattext")
                mattext.text = str(p.value)
        
        # Add resprocessing element
        resprocessing = ET.SubElement(item_element, "resprocessing")
        outcomes = ET.SubElement(resprocessing, "outcomes")
        ET.SubElement(outcomes, "decvar", maxvalue="100", minvalue="0", varname="SCORE", vartype="Decimal")
        
        # Add conditions for each pair
        for i, pair in enumerate(item.pairs, start=1):
            respcondition = ET.SubElement(resprocessing, "respcondition")
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            varequal = ET.SubElement(conditionvar, "varequal", respident=f"response{i}")
            varequal.text = f"label{i}"
            setvar = ET.SubElement(respcondition, "setvar", action="Add", varname="SCORE")
            setvar.text = str(100.0 / len(item.pairs))

            # if comment exists in item
            if pair.explanation:
                respcondition = ET.SubElement(resprocessing, "respcondition")
                conditionvar = ET.SubElement(respcondition, "conditionvar")
                notconditionvar = ET.SubElement(conditionvar, "not")
                varequal = ET.SubElement(notconditionvar, "varequal", respident=f"response{i}")
                varequal.text = f"label{i}"
                ident = f"comment{i}"
                ET.SubElement(respcondition, "displayfeedback", feedbacktype="Response", linkrefid=ident)

        for i, pair in enumerate(item.pairs, start=1):
            # Add item feedback
            if pair.explanation:
                ident = f"comment{i}"
                itemfeedback = ET.SubElement(item_element, "itemfeedback", ident=ident)
                flow_mat = ET.SubElement(itemfeedback, "flow_mat")
                material = ET.SubElement(flow_mat, "material")
                mattext = ET.SubElement(material, "mattext")
                mattext.text = str(pair.explanation)

        # Add general feedback (explanation)
        self._add_general_feedback(item_element, item)
