#!/usr/bin/env python3
# from prettytable import PrettyTable
import os
import pymupdf
import regex
import math
from collections import defaultdict
from PIL import Image


class ImageGen:
    def __init__(self, cfg, start_page, end_page, chapter):
        self.cfg = cfg
        self.start_page = start_page
        self.end_page = end_page
        self.chapter = chapter

    def merge_pages_to_single(self):
        doc = pymupdf.open(self.cfg.input_file_pdf)
        spage = self.start_page
        epage = self.end_page

        # Check if the provided pages are within bounds
        if spage < 0 or epage >= doc.page_count:
            raise ValueError("Page numbers out of bounds.")

        # Calculate total height required for the composite page
        total_height = 0
        page_width = 0

        for page_num in range(spage, epage + 1):
            original_page = doc.load_page(page_num)
            rect = original_page.rect
            total_height += rect.height
            page_width = max(page_width, rect.width)  # Get the maximum width

        # Create a new blank page with the total height and maximum width
        new_pdf = pymupdf.open()
        composite_page = new_pdf.new_page(width=page_width, height=total_height)

        y_offset = 0  # Vertical offset to place the pages one after the other

        # Loop through the specified range of pages and add them to the composite page
        for page_num in range(spage, epage + 1):
            original_page = doc.load_page(page_num)
            rect = original_page.rect
            
            # Insert the content of the original page into the composite page
            composite_page.show_pdf_page(pymupdf.Rect(0, y_offset, rect.width, y_offset + rect.height), doc, page_num)

            # Update the y_offset for the next page
            y_offset += rect.height

        # Save the output
        doc.close()
        output_pdf = "out.pdf"
        new_pdf.save(output_pdf)
        print(f"Composite PDF created and saved as '{output_pdf}'.")
        # new_pdf.close()
        return new_pdf

    def find_approximate_match(self, concat_text, search_string):
        """
        Find the approximate match of a search_string in concat_text using regex with fuzzy matching.
        The function loops over max_edits from 0 upwards until a match is found.
        
        Parameters:
            concat_text (str): The large text to search in.
            search_string (str): The string to find approximately.
            max_allowed_edits (int): The maximum number of edits to attempt before stopping.
        
        Returns:
            (start_index, end_index, max_edits): A tuple with the start and end index of the match and the number of edits used.
        """
        max_edits = 0
        while True:
            max_edits += 1
            # Build the fuzzy search pattern with regex allowing for `max_edits` edits.
            pattern = f"(?e)({regex.escape(search_string)}){{e<={max_edits}}}"
            
            # Search the entire concat_text for the pattern
            match = regex.search(pattern, concat_text)
            
            if match:
                # Return the start and end index of the match and the number of edits used
                return match.start(), match.end(), sum(match.fuzzy_counts)
        
        # If no match is found after reaching max_allowed_edits, return None
        return None, None, None

    def find_matching_blocks(self, blocks, quotes):

        # Concatenate block texts with block numbers
        concat_text = ""
        block_number_map = {}
        for i, block in enumerate(blocks):
            x0, y0, x1, y1, block_text, block_no, block_type = block
            if block_type == 1:     # image block
                continue
            beg_idx = len(concat_text) - 1
            end_idx = beg_idx + len(block_text)
            concat_text += block_text + " "
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
        errors = {}
        for ident, ql in quotes.items():
            for quote in ql:
                beg_loc, end_loc, num_err = self.find_approximate_match(concat_text, quote)
                errors[quote] = num_err
                if beg_loc is not None and end_loc is not None:
                    for i, (beg_idx, end_idx) in block_number_map.items():
                        case1 = beg_idx >= beg_loc and beg_idx <= end_loc
                        case2 = end_idx >= beg_loc and end_idx <= end_loc
                        case3 = beg_idx <= beg_loc and end_idx >= end_loc
                        if case1 or case2 or case3:
                            matching_blocks[ident].append(blocks[i][:4])
                        # if regex.match("Theodor Schwann",quote):
                        #    print(f"{beg_idx} v {beg_loc} and e={end_idx} v {end_loc} : {case1} {case2} {case3}")
        for ident, ql in quotes.items():
            if not matching_blocks[ident]:
                print(f" missing image for {ql}")
        return matching_blocks

    def double_bounding_rect(self, bounding_rect):
        """
        Double the size of the bounding rectangle in all directions.
        """
        # Calculate the center of the rectangle
        center_x = (bounding_rect.x0 + bounding_rect.x1) / 2
        center_y = (bounding_rect.y0 + bounding_rect.y1) / 2
        
        # Calculate the current width and height
        width = bounding_rect.width
        height = bounding_rect.height
        
        # Double the size by expanding equally on all sides
        new_rect = pymupdf.Rect(
            center_x - width,   # new x0
            center_y - height,  # new y0
            center_x + width,   # new x1
            center_y + height   # new y1
        )
        
        return new_rect

    def save_block_images(self, matching_blocks, page):
        """
        Highlights the text blocks in a PDF page, extracts the highlighted area,
        zooms out by 2x, and saves the resulting image.

        Parameters:
            matching_blocks (dict): A dictionary with quotes as keys and corresponding text blocks as values.
            page (fitz.Page): The page object from the PyMuPDF library.
            output_path (str): The path where the image will be saved.
        """
        
        # Set the scale factor for zooming out (2x zoom out means scaling to 50%)

        quote_images = {}

        zoom_out_scale = 10
        counter = 0
        num_blocks = len(matching_blocks)
        if num_blocks:
            padding_width = math.ceil(math.log10(num_blocks + 1))
        
        # Iterate over the matching quotes and their blocks
        for ident, blocks in matching_blocks.items():
            page.add_highlight_annot(blocks)

            # Calculate the bounding box that surrounds all the blocks
            bounding_rect = pymupdf.Rect()
            for block in blocks:
                block_rect = pymupdf.Rect(block)  # Get the block rectangle
                bounding_rect |= block_rect    # Union with the overall bounding box
            
            # Create a 2D transformation matrix to zoom the page out (scaling down)
            mat = pymupdf.Matrix(zoom_out_scale, zoom_out_scale)
            
            # Render the entire page as a pixmap (image)
            double_bounding_rect = self.double_bounding_rect(bounding_rect)
            pix = page.get_pixmap(matrix=mat, clip=double_bounding_rect)  #
            image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            counter += 1
            imgname = f"{self.chapter}/img{counter:0{padding_width}}.png"
            output_file = f"{self.cfg.output_dir_png}/{imgname}"
            dirname = os.path.dirname(output_file)
            os.makedirs(dirname, exist_ok=True)
            image.save(output_file)
            quote_images[ident] = imgname

        return quote_images

    def generate(self, quotes):
        doc = self.merge_pages_to_single()
        page = doc[0]
        tpage = page.get_textpage()
        blocks = tpage.extractBLOCKS()
        matching_blocks = self.find_matching_blocks(blocks, quotes)
        quote_images = self.save_block_images(matching_blocks, page)
        doc.close()
        return quote_images


if __name__ == "__main__":
    pass
