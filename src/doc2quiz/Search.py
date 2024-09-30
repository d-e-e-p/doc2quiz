#!/usr/bin/env python3
import regex
import wordninja
import string
from collections import defaultdict
from neofuzz import char_ngram_process
from neofuzz import Process
from sklearn.feature_extraction.text import TfidfVectorizer
from langchain_text_splitters import RecursiveCharacterTextSplitter

# from prettytable import PrettyTable


class Search:
    def __init__(self, cfg):
        self.cfg = cfg
        self.debug_match = True

    def setup_nprocess(self, n_chars, passage):
        min_chunk_size = 200
        chunk_size = max(1.3 * n_chars, min_chunk_size)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_size / 2,
            length_function=len,
            is_separator_regex=False,
        )
        docs = text_splitter.create_documents([passage])
        sentences = [doc.page_content for doc in docs]

        vectorizer = TfidfVectorizer()
        # self.nprocess = char_ngram_process()
        nprocess = Process(vectorizer, metric="cosine")
        nprocess.index(sentences)
        return nprocess

    def find_fuzzy_and_regex(self, ident, passage, search_string):
        """
        find the closest matching sentence
        each sentence is a snippet of the same length as search string
        """
        threshold = 10
        n_chars = len(search_string)

        print(f"setip {search_string}")
        self.setup_nprocess(n_chars, passage)
        print("match")
        best_match, similarity = self.nprocess.extractOne(search_string)

        if self.debug_match:
            print("------------")
            print(f"fm quote      {ident} : {search_string}")
            print(f"fm Best match {ident}: {best_match}")
            print(f"fm Similarity:{ident}: {similarity}")

        if best_match and similarity > threshold:
            # Find the starting index of the match in the original passage
            find_idx = passage.find(best_match)
        else:
            find_idx = -1
            if self.debug_match:
                print("No reasonable match found. Using the entire text.")

        # create partial string and offset
        if find_idx >= 0:
            start_idx = find_idx
            end_idx = find_idx + n_chars
        else:
            start_idx = 0
            end_idx = len(passage)
           
        # refine the search if regex_search if defined
        if find_idx == -1:
            if self.debug_match:
                partial_text = passage[start_idx:end_idx]
                print(f"fm no_regex_search so return  partial text match = {partial_text}")
            return None, None, None

        # do regex search
        if find_idx >= 0:
            padding_chars = 100
            start_idx = max(start_idx - padding_chars, 0)
            end_idx = min(end_idx + padding_chars, len(passage))
            if self.debug_match:
                partial_text = passage[start_idx:end_idx]
                print(f"ft regex_search using partial_text = {partial_text}")

        partial_text = passage[start_idx:end_idx]
        beg_loc, end_loc, num_err = self.find_regex(partial_text, search_string)
        if beg_loc is not None and end_loc is not None:
            beg_loc += start_idx
            end_loc += start_idx
            return beg_loc, end_loc, num_err

        if find_idx >= 0:
            return start_idx, end_idx, similarity
        else:
            return None, None, None

    def preprocess_hyphen_newline(self, text, hyphen_newline=' -\n', replacement=''):
        """
        Removes all occurrences of a string like ' -\n' from the given text and keeps track of positions.

        Parameters:
        text (str): The input text.

        Returns:
        tuple: A tuple containing the preprocessed text and a list of positions where ' -\n' was removed.
        """
        positions = []
        preprocessed_text = ""
        i = 0
        while i < len(text):
            if text[i:i + len(hyphen_newline)] == hyphen_newline:
                positions.append(i)
                i += len(hyphen_newline)
                preprocessed_text += replacement
            else:
                preprocessed_text += text[i]
                i += 1
        return preprocessed_text, positions

    def reinsert_hyphen_newline(self, text, positions, target_string, hyphen_newline=' -\n', replacement=''):
        """
        Re-inserts ' -\n' back into the text at the specified positions, adjusted for offset.

        Parameters:
        text (str): The input text.
        positions (list): The list of positions where ' -\n' was removed.
        offset (int): The offset to adjust positions.

        Returns:
        str: The text with ' -\n' re-inserted.
        """
        offset = text.index(target_string)
        length = len(target_string)
        snippet = text[offset:offset + length]

        accumulated_spaces = 0
        for pos in positions:
            adjusted_pos = pos - offset - accumulated_spaces
            if adjusted_pos < 0:
                accumulated_spaces += len(hyphen_newline) - len(replacement)
            elif adjusted_pos < len(snippet):
                snippet = snippet[:adjusted_pos] + hyphen_newline + snippet[adjusted_pos + len(replacement):]
            else:
                # adjusted_pos is past the snippet..
                return snippet

        # in case positions is empty
        return snippet
        

    def find_regex(self, passage, search_string):
        """
        Find the approximate match of a search_string in passage using regex with fuzzy matching.
        The function loops over max_edits from 0 upwards until a match is found.
        
        Parameters:
            passage (str): The large text to search in.
            search_string (str): The string to find approximately.
            max_allowed_edits (int): The maximum number of edits to attempt before stopping.
        
        Returns:
            (start_index, end_index, max_edits): A tuple with the start and end index of the match and the number of edits used.
        """
        if self.debug_match:
            print(f"find_regex : search string={search_string}")
            if len(passage) > 5000:
                print(f"find_regex: entire text of length {len(passage)}")
            else:
                print(f"find_regex : target string={passage}")

        # limit max_edits to 10 or 10% of short quote
        max_edits = min(10, len(search_string) * 0.1)
        edits = 0
        while edits < max_edits:
            # Build the fuzzy search pattern with regex allowing for `max_edits` edits.
            pattern = f"(?e)(?i)({regex.escape(search_string)}){{e<={edits}}}"
            edits += 1
            if self.debug_match:
                print(f" {edits} ", end="", flush=True)
            match = regex.search(pattern, passage)

            if match:
                print(f" match: {match}")
                # Re-insert ' -\n' back into the matched string
                matched_string = match.group(0)
                match_start = match.start(0)
                try:
                    match_start = passage.index(matched_string)
                except ValueError:
                    breakpoint()
                    return None, None, None
                match_end = match_start + len(matched_string)
                return match_start, match_end, sum(match.fuzzy_counts)

        print(f" match: {match} max_edits={max_edits}")
        # give up
        return None, None, None

    def find_quote_in_passage(self, ident, passage, search_string):
        """
        """
        # modify original text to remove pdf extraction artifacts
        intext1, positions1 = self.preprocess_hyphen_newline(passage, hyphen_newline=' -\n')
        intext2, positions2 = self.preprocess_hyphen_newline(intext1, hyphen_newline='-\n')
        intext3, positions3 = self.preprocess_hyphen_newline(intext2, hyphen_newline='\n', replacement=' ')
        intext4, positions4 = self.preprocess_joinedwords(intext3)

        beg_loc, end_loc, num_err = self.find_fuzzy_and_regex(ident, intext4, search_string)

        if beg_loc is None or end_loc is None:
            if self.debug_match:
                print("find_quote_in_passage : empty handed")
            return None, None, None
    
        matched_string = intext4[beg_loc:end_loc]

        snippet1 = self.reinsert_joinedwords(intext4, positions4, matched_string)
        snippet2 = self.reinsert_hyphen_newline(intext3, positions3, snippet1, hyphen_newline='\n', replacement=' ')
        snippet3 = self.reinsert_hyphen_newline(intext2, positions2, snippet2, hyphen_newline='-\n')
        snippet4 = self.reinsert_hyphen_newline(intext1, positions1, snippet3, hyphen_newline=' -\n')
        try:
            match_start = passage.index(snippet4)
        except ValueError:
            breakpoint()
            return None, None, None
        match_end = match_start + len(snippet3)
        # print(f" match_start = {match_start}")
        # Return the start and end index of the match and the number of edits used
        if self.debug_match:
            print(f"find_quote_in_passage : found q={snippet4}")
        return match_start, match_end, num_err


    def find_matching_blocks(self, blocks, quotes):

        # Concatenate block texts with block numbers
        passage = ""
        block_number_map = {}
        for i, block in enumerate(blocks):
            x0, y0, x1, y1, block_text, block_no, block_type = block
            if block_type == 1:     # image block
                continue
            beg_idx = len(passage) - 1
            end_idx = beg_idx + len(block_text)
            passage += block_text + " "
            block_number_map[i] = (beg_idx, end_idx)

        # ok, now look for each quote
        # idx is for each block
        # loc is matched locations.
        # case1:
        #       beg_idx >---------
        #   beg_loc>----------<end_loc
        # case2:
        #       ---------< end_idx
        #   beg_loc>----------<end_loc
        # case3:
        #   begg_idx>---------< end_idx
        #        beg_loc>---<end_loc
        matching_blocks = defaultdict(list)
        for ident, ql in quotes.items():
            for quote in ql:
                blocks_per_quote = []
                beg_loc, end_loc, num_err = self.find_quote_in_passage(ident, passage, quote)
                # beg_loc, end_loc = quote.start_ptr + quote_ptr_offset, quote.end_ptr + quote_ptr_offset
                # print(f"\n------------------\nquote = {beg_loc}:{end_loc}")
                if beg_loc is not None and end_loc is not None:
                    for i, (beg_idx, end_idx) in block_number_map.items():
                        case1 = beg_idx >= beg_loc and beg_idx <= end_loc
                        case2 = end_idx >= beg_loc and end_idx <= end_loc
                        case3 = beg_idx <= beg_loc and end_idx >= end_loc
                        if case1 or case2 or case3:
                            blocks_per_quote.append(blocks[i][:4])
                        # if regex.match("Theodor Schwann",quote):
                        #    print(f"{beg_idx} v {beg_loc} and e={end_idx} v {end_loc} : {case1} {case2} {case3}")
                    matching_blocks[ident].append(blocks_per_quote)
                    print(f"matching_blocks for ident {ident} = {len(matching_blocks[ident])}")
        for ident, ql in quotes.items():
            if not matching_blocks[ident]:
                print(f" missing matcking block for {ql}")
        return matching_blocks


    def preprocess_joinedwords(self, text):
        """
        Segments concatenated words using wordninja while maintaining spaces, newlines, punctuation, 
        numbers, and other non-alphabetic characters. Keeps track of positions where splits occur.

        Parameters:
        text (str): The input text with spaces, newlines, punctuation, numbers, and concatenated words.

        Returns:
        tuple: A tuple containing the preprocessed text and a list of positions where splits occurred.
        """
        positions = []
        preprocessed_text = ""
        i = 0
        while i < len(text):
            # Check for space, tab, or newline and preserve them
            if text[i].isspace():
                preprocessed_text += text[i]
                i += 1
            # Check for punctuation or numbers and preserve them as-is
            elif text[i] in string.punctuation or text[i].isdigit():
                preprocessed_text += text[i]
                i += 1
            else:
                # Extract the next word-like segment (until encountering a space or special character)
                start = i
                while i < len(text):
                    i += 1
                word = text[start:i]
                
                # Use wordninja to split the word if it's a pure alphabetic word
                if word.isalpha():
                    split_words = wordninja.split(word)
                    if len(split_words) > 1:  # Only track positions if a split occurred
                        positions.append((len(preprocessed_text), word))  # Track original word position
                    preprocessed_text += ' '.join(split_words)
                else:
                    # If it's not alphabetic, don't split it
                    preprocessed_text += word
        
        return preprocessed_text, positions


    def reinsert_joinedwords(self, text, positions, target_string):
        """
        Re-inserts original concatenated words back into a target snippet of the text starting at the given offset,
        only reinserting spaces back in the provided target string.

        Parameters:
        text (str): The input text (with wordninja splits).
        positions (list): The list of positions where original words were split.

        Returns:
        str: The snippet of text with spaces reinserted into concatenated words.
        """
        # Extract the target snippet from the text using the provided offset and length
        offset = text.index(target_string)
        length = len(target_string)
        snippet = text[offset:offset + length]
        print(f"reinsert_joinedwords:  offset = {offset} len={length}")
        
        # Iterate over positions and find those that apply within the snippet range
        for pos, original_word in positions:
            adjusted_pos = pos - offset
            if 0 <= adjusted_pos < len(snippet):
                # Calculate the split length of the word (this is the space-inserted version length)
                split_words = wordninja.split(original_word)
                split_length = len(' '.join(split_words))  # Length of the split version with spaces
                
                # Replace the space-inserted version with the original concatenated word in the snippet
                snippet = snippet[:adjusted_pos] + original_word + snippet[adjusted_pos + split_length:]
        
        return snippet

    def find_exact_quote(self, quote):
        """
            the quote string in self.text might not be exact...
        """
        return self.find_fuzzy_search(quote)

def test_worksplit():
    text = """
    mightiestcommercial is a normal:
        1. spaceflightlaunch   
        2. successlandingspectacular
    test

    """

    print(f" test1: test_split")
    search = Search({})
    intext1 , positions1 = search.preprocess_joinedwords(text)
    print("Orig text       :", text)
    print("Preprocessed text:", intext1)
    print("Positions:", positions1)

    # Re-insert concatenated words starting from a given offset (e.g., at "spaceflightlaunch")
    target_string = "1. spaceflight launch"
    snippet = search.reinsert_joinedwords(intext1, positions1, target_string)
    print("Reconstructed snippet:", snippet)

    print(" test2: regex")
    search_string = "1. spaceflightlaunch"
    beg_loc, end_loc, num_err = search.find_regex(text, search_string)
    print(f" found target_string at ({beg_loc} , {end_loc}) with err={num_err}")

def test_search():
    search_string="""America’s population was still about 90 percent rural, despite the flourishing cities. All but 5 percent of the people lived east of the Appalachian Mountains."""
    target_string="""impo-
ssible. The eyes of a skeptical world
were on the upstart United States.
 Growing Pains
 When the Constitution was launched in 1789, the
Rep -
ublic was continuing to grow at an amazing rate.
Population was doubling about every twenty-five
years, and the first official census of 1790 recorded
almost 4 million people. Cities had blossomed pro-
portionately: Philadelphia numbered 42,000, New
York 33,000, Boston 18,000, Charleston 16,000, and
Baltimore 13,000.
    A -
me -
rica’s pop -
ulation was still about 90 percent
rural, des -
pite the flourishing cities. All but 5 percent
of the people lived east of the Appalachian Moun-
tains. The trans-Appalachian overflow was concen-
tra"""

    search = Search({})
    beg_loc, end_loc, num_err = search.find_regex(target_string, search_string)
    print(f" found search_string at ({beg_loc} , {end_loc}) with err={num_err}")
    

if __name__ == "__main__":
    # test_worksplit()
    test_search()
