#!/usr/bin/env python3
import regex
from neofuzz import char_ngram_process
# from prettytable import PrettyTable


class Search:
    def __init__(self, cfg, text):
        self.cfg = cfg
        self.text = text
        self.debug_match = True
        self.nprocess = None

    def find_fuzzy_search(self, search_string):

        concat_text = self.text

        # find the closest matching sentence
        # each sentence is a snippet of the same length as search string

        n_chars = len(search_string)
        n_chars_half = round(n_chars)
        if self.nprocess is None:
            offset = 0
            pieces = []
            while offset < len(concat_text):
                pieces.append(concat_text[offset:offset + n_chars_half])
                offset += n_chars_half
            sentences = [pieces[i] + pieces[i + 1] + pieces[i + 2] for i in range(len(pieces) - 2)]
            self.nprocess = char_ngram_process()
            self.nprocess.index(sentences)

        best_match, similarity = self.nprocess.extractOne(search_string)

        # match = process.extractOne(search_string, sentences, score_cutoff=threshold)

        if self.debug_match:
            print("------------")

        if best_match:
            if self.debug_match:
                print(f"fm quote     : {search_string}")
                print(f"fm Best match: {best_match}")
                print(f"fm Similarity: {similarity}")
            
            # Find the starting index of the match in the original concat_text
            find_idx = concat_text.find(best_match)
            if self.debug_match:
                print(f"fm find_idx = {find_idx}")
            
        else:
            find_idx = -1
            if self.debug_match:
                print("No reasonable match found. Using the entire text.")

        # create partial string and offset
        if find_idx >= 0:
            start_idx = find_idx
            end_idx = find_idx + 3 * n_chars_half
        else:
            start_idx = 0
            end_idx = len(concat_text)
           
        print(f"fm find_idx = {find_idx} so start_idx={start_idx} end end_idx={end_idx}")

        # refine the search if regex_search if defined
        no_regex_search = False
        if no_regex_search and find_idx >= 0:
            if self.debug_match:
                partial_text = concat_text[start_idx:end_idx]
                print(f"fm no_regex_search return partial_text = {partial_text}")
            return partial_text

        # else

        if find_idx >= 0:
            padding_chars = 100
            start_idx = max(start_idx - padding_chars, 0)
            end_idx = min(end_idx + padding_chars, len(concat_text))
            if self.debug_match:
                partial_text = concat_text[start_idx:end_idx]
                print(f"ft regex_search using partial_text = {partial_text}")

        partial_text = concat_text[start_idx:end_idx]
        return self.find_regex_search(partial_text, search_string)

    def preprocess_text_to_match(self, text):
        """
        Removes all occurrences of ' -\n' from the given text and keeps track of positions.

        Parameters:
        text (str): The input text.

        Returns:
        tuple: A tuple containing the preprocessed text and a list of positions where ' -\n' was removed.
        """
        positions = []
        preprocessed_text = ""
        i = 0
        while i < len(text):
            if text[i:i + 3] == " -\n":
                positions.append(i)
                i += 3
            else:
                preprocessed_text += text[i]
                i += 1
        return preprocessed_text, positions

    def reinsert_hyphen_newline(self, text, positions, offset):
        """
        Re-inserts ' -\n' back into the text at the specified positions, adjusted for offset.

        Parameters:
        text (str): The input text.
        positions (list): The list of positions where ' -\n' was removed.
        offset (int): The offset to adjust positions.

        Returns:
        str: The text with ' -\n' re-inserted.
        """
        for pos in positions:
            adjusted_pos = pos - offset
            if 0 <= adjusted_pos < len(text):
                text = text[:adjusted_pos] + " -\n" + text[adjusted_pos:]
        return text

    def find_regex_search(self, search_string, text):
        """
        Find the approximate match of a search_string in text using regex with fuzzy matching.
        """
        if self.debug_match:
            print(f"find_regex_search : looking for q={search_string}")
            if len(text) > 5000:
                print("find_regex_search: entire concat")
            else:
                print(f"find_regex_search : target string={text}")

        max_edits = 10
        edits = 0
        preprocessed_text_to_match, positions = self.preprocess_text_to_match(text)
        while edits < max_edits:
            # Build the fuzzy search pattern with regex allowing for `max_edits` edits.
            pattern = f"(?e)(?i)({regex.escape(search_string)}){{e<={edits}}}"
            edits += 1
            if self.debug_match:
                print(f" {edits} ", end="", flush=True)
            match = regex.search(pattern, preprocessed_text_to_match)

            if match:
                # Re-insert ' -\n' back into the matched string
                matched_string = match.group(0)
                match_start = match.start(0)
                reinserted_string = self.reinsert_hyphen_newline(matched_string, positions, match_start)
                # Return the start and end index of the match and the number of edits used
                if self.debug_match:
                    print(" ")
                    print(f"find_regex_search : found       q={matched_string}")
                    print(f"find_regex_search : done with {match.fuzzy_counts} total {sum(match.fuzzy_counts)}")
                return reinserted_string

        # give up and return fuzzy search results
        if len(text) < 1000:
            return text

        # really give up
        return None

    def find_exact_quote(self, quote):
        """
            the quote string in self.text might not be exact...
        """
        return self.find_fuzzy_search(quote)


if __name__ == "__main__":
    pass
