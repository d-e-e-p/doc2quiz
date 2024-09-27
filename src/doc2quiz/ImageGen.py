#!/usr/bin/env python3
# from prettytable import PrettyTable
import os
import pymupdf
import regex
import math
from collections import defaultdict
from PIL import Image
from .Search import Search

class ImageGen:
    def __init__(self, cfg, start_page, end_page, chapter):
        self.cfg = cfg
        self.start_page = start_page
        self.end_page = end_page
        self.chapter = chapter
        self.debug_match = True
        self.nprocess = None
        self.search = Search(self.cfg)

    def merge_pages_to_single(self):
        doc = pymupdf.open(self.cfg.input_file_pdf)
        spage = self.start_page
        epage = self.end_page

        # Check if the provided pages are within bounds
        freak_out_about_page_ranges = False
        if freak_out_about_page_ranges:
            if spage < 0 or epage >= doc.page_count:
                raise ValueError("Page numbers out of bounds.")
        else:
            if spage < 0:
                spage = 0
            if epage >= doc.page_count:
                epage = doc.page_count - 1

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

        # need to new_pdf.close() later...
        return new_pdf

    def scale_bounding_rect(self, bounding_rect, scale_factor):
        """
        Scale the size of the bounding rectangle in all directions by a specified factor.
        
        :param bounding_rect: The original bounding rectangle.
        :param scale_factor: The factor by which to scale the rectangle (e.g., 0.5 to halve, 2.0 to double).
        :return: A new scaled Rect object.
        """
        # Calculate the center of the rectangle
        center_x = (bounding_rect.x0 + bounding_rect.x1) / 2
        center_y = (bounding_rect.y0 + bounding_rect.y1) / 2

        # Calculate the current width and height
        width = bounding_rect.width
        height = bounding_rect.height

        # Scale the width and height by the scale_factor
        new_width = width * scale_factor
        new_height = height * scale_factor

        # Create the new scaled rectangle by expanding or shrinking equally from the center
        new_rect = pymupdf.Rect(
            max(0, center_x - new_width / 2),   # new x0
            max(0, center_y - new_height / 2),  # new y0
            center_x + new_width / 2,   # new x1
            center_y + new_height / 2   # new y1
        )

        return new_rect

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

    def mark_intersecting_blocks(self, blocks, page):
        
        # Convert block tuples to Rect objects and store them with original block
        block_rects = [(pymupdf.Rect(block[:4]), block) for block in blocks]

        # Create a list to store groups of intersecting block rects
        intersecting_groups = []

        # Compare blocks to find intersecting ones
        for rect, block in block_rects:
            added_to_group = False
            # Check against existing groups
            for group in intersecting_groups:
                # If rect intersects with any block in the group, add to group
                if any(rect.intersects(other_rect) for other_rect, _ in group):
                    group.append((rect, block))
                    added_to_group = True
                    break
            
            # If not added to any group, create a new group
            if not added_to_group:
                intersecting_groups.append([(rect, block)])

        # Draw rectangles for each group
        for group in intersecting_groups:
            # Combine intersecting rectangles into one larger rectangle
            combined_rect = pymupdf.Rect()
            for rect, _ in group:
                combined_rect.include_rect(rect)
            
            # Draw the combined rectangle on the page
            scaled_rect = self.scale_bounding_rect(combined_rect, 1.1)
            page.draw_rect(scaled_rect, color=(0, 0, 1), width=2, radius=0.1)

    def delete_all_annot(self, page):
        annot = page.first_annot
        breakpoint()
        
        # Iterate over all annotations and delete them
        while annot:
            page.delete_annot(annot)  # Delete the current annotation
            # Update to the next annotation (because list changes after deletion)
            annot = page.first_annot

    def save_highlight_images(self, quotes, page, doc):
        """
        Highlights the text blocks in a PDF page, extracts the highlighted area,
        zooms out by 2x, and saves the resulting image.
        """
        highlight_text_box = False
        
        quote_images = defaultdict(list)

        # Set the scale factor for zooming out (2x zoom out means scaling to 50%)
        zoom_out_scale = 10
        counter = 0

        padding_width = 2

        # Iterate over the matching quotes and their blocks
        for ident, ql in quotes.items():
            for search_string in ql:
                # create temp copy of pdf for markup
                tmp_doc = pymupdf.open()
                # tmp_doc.delete_page(0)
                tmp_page = tmp_doc.new_page(width=page.rect.width, height=page.rect.height)
                tmp_page.show_pdf_page(page.rect, doc)

                rects = page.search_for(search_string, quads=False)

                if not rects:
                    breakpoint()

                for rect in rects:
                    tmp_page.add_highlight_annot(rect)

                bounding_rect = pymupdf.Rect()
                for rect in rects:
                    hilight_rect = pymupdf.Rect(rect)  # Get the block rectangle
                    bounding_rect |= hilight_rect    # Union with the overall bounding box

                # Create a 2D transformation matrix to zoom the page out (scaling down)
                mat = pymupdf.Matrix(zoom_out_scale, zoom_out_scale)
                
                # Render the entire page as a pixmap (image)
                double_bounding_rect = self.scale_bounding_rect(bounding_rect, 2.0)
                double_bounding_rect = double_bounding_rect & page.rect
                pix = tmp_page.get_pixmap(matrix=mat, clip=double_bounding_rect)  #
                image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                counter += 1
                imgname = f"{self.chapter}/img{counter:0{padding_width}}.png"
                output_file = f"{self.cfg.output_dir_png}/{imgname}"
                dirname = os.path.dirname(output_file)
                os.makedirs(dirname, exist_ok=True)
                image.save(output_file)
                quote_images[ident].append(imgname)
                # self.delete_all_annot(tmp_page)
                tmp_doc.close()
            
        return quote_images

    def save_block_images(self, matching_blocks, page, doc):
        """
        Highlights the text blocks in a PDF page, extracts the highlighted area,
        zooms out by 2x, and saves the resulting image.
        """
        highlight_text_box = False

        print("save_block_images:")
        
        quote_images = defaultdict(list)

        # Set the scale factor for zooming out (2x zoom out means scaling to 50%)
        zoom_out_scale = 5
        counter = 0
        num_blocks = sum(len(values) for values in matching_blocks.values())
        if num_blocks:
            padding_width = math.ceil(math.log10(num_blocks + 1))


        # Iterate over the matching quotes and their blocks
        for ident, block_lol in matching_blocks.items():
            for blocks in block_lol:
                # create temp copy of pdf for markup
                tmp_doc = pymupdf.open()
                # tmp_doc.delete_page(0)
                tmp_page = tmp_doc.new_page(width=page.rect.width, height=page.rect.height)
                tmp_page.show_pdf_page(page.rect, doc)

                if highlight_text_box:
                    tmp_page.add_highlight_annot(blocks)
                self.mark_intersecting_blocks(blocks, tmp_page)

                # Calculate the bounding box that surrounds all the blocks
                # Calculate the bounding box that surrounds all the blocks
                bounding_rect = pymupdf.Rect()
                for block in blocks:
                    block_rect = pymupdf.Rect(block)  # Get the block rectangle
                    bounding_rect |= block_rect    # Union with the overall bounding box
            
                # Create a 2D transformation matrix to zoom the page out (scaling down)
                mat = pymupdf.Matrix(zoom_out_scale, zoom_out_scale)
                
                # Render the entire page as a pixmap (image)
                imgname = f"{self.chapter}/img{counter:0{padding_width}}.png"

                double_bounding_rect = self.scale_bounding_rect(bounding_rect, 2.0)
                double_bounding_rect = double_bounding_rect & page.rect
                pix = tmp_page.get_pixmap(matrix=mat, clip=double_bounding_rect)  #

                try:
                    # Attempt to create an image from raw data
                    image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                    print(f" image {imgname} {pix.width} x {pix.height}")
                    counter += 1
                    output_file = f"{self.cfg.output_dir_png}/{imgname}"
                    dirname = os.path.dirname(output_file)
                    os.makedirs(dirname, exist_ok=True)
                    image.save(output_file)
                    quote_images[ident].append(imgname)
                    
                except ValueError as e:
                    print(f"Error creating image from pixmap: {e}")

                except Exception as e:
                    print(f"An unexpected error occurred: {e}")


                # self.delete_all_annot(tmp_page)
                tmp_doc.close()
            
        return quote_images

    def generate(self, quotes, chapter):
        # save composite pdf
        doc = self.merge_pages_to_single()
        output_pdf = f"{self.cfg.output_dir_pdf}/{chapter}.pdf"
        doc.save(output_pdf)
        print(f"Composite PDF saved as '{output_pdf}'.")

        page = doc[0]
        tpage = page.get_textpage()
        blocks = tpage.extractBLOCKS()
        matching_blocks = self.search.find_matching_blocks(blocks, quotes)
        quote_images = self.save_block_images(matching_blocks, page, doc)
        # quote_images = self.save_highlight_images(quotes, page, doc)

        doc.close()
        print("done with imagegen")
        return quote_images


if __name__ == "__main__":
    pass
