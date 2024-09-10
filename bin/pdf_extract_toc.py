#!/usr/bin/env python3.10
import sys
import csv
import pymupdf

# used chatGPT prompt to generate

def extract_end_pages(toc):
    """
    Determine the end pages for each section in the TOC.
    The end page of a section is either the start page of the next section
    (depending on the section level) or the end of the document.
    """
    toc_with_page_end = []
    
    # Iterate over the toc entries
    for i, (level, title, start_page) in enumerate(toc):
        end_page = None
        
        # Determine the end page for the current section
        for j in range(i + 1, len(toc)):
            next_level, next_title, next_start_page = toc[j]
        
            # is this page the same level?
            if next_level == level:
                end_page = next_start_page - 1
                # print(f"{j} EQ {next_level == level} l={level} t={title} p={start_page} to l={next_level} t={next_title} p={end_page}")
                break
            elif next_level <= level:
                # print(f" LT l={level} t={title} p={start_page} to l={next_level} t={next_title} p={end_page}")
                end_page = next_start_page - 1
                break
            else:
                # print(f"{j} skipping l={level} t={title} p={start_page} to l={next_level} t={next_title} p={end_page}")
                pass

        # If no subsequent section is found that satisfies the end condition, assume end of document
        if end_page is None:
            end_page = doc.page_count - 1  # Assuming doc is a global or passed variable

        if end_page < start_page:
            end_page = start_page

        # Append the current section with its end page to the new TOC
        toc_with_page_end.append((start_page, end_page, level, title))
    
    return toc_with_page_end


def print_toc_as_csv(toc_with_page_end, output_file=None):
    """
    Print the TOC with end pages in CSV format.
    If output_file is specified, the CSV will be saved to the file.
    Otherwise, it will be printed to the console.
    """
    # Define the header
    header = ['StartPage', 'EndPage', 'Level', 'Title']

    if output_file:
        # Write to a file
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(header)
            writer.writerows(toc_with_page_end)
    else:
        # Print to the console
        writer = csv.writer(sys.stdout)
        writer.writerow(header)
        writer.writerows(toc_with_page_end)


def print_toc_indented(toc_with_page_end):
    """
    Print the TOC with end pages as a tab-indented list.
    The indentation depends on the level of the section.
    """
    for start_page, end_page, level, title in toc_with_page_end:
        num_pages = end_page - start_page + 1
        indent = '\t' * (level - 1)
        print(f"{indent}{title} ({num_pages} pages)")


if __name__ == "__main__":
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python pdf_extract_toc.py <pdf_filename>")
        print(f"Usage: len(sys.argv)={len(sys.argv)}")
        sys.exit(1)

    pdf_filename = sys.argv[1]
    doc = pymupdf.open(pdf_filename)
    toc = doc.get_toc()  # Get the table of contents

    output_file = sys.argv[2] if len(sys.argv) == 3 else None

    toc_with_page_end = extract_end_pages(toc)
    print_toc_indented(toc_with_page_end)
    if output_file:
        print_toc_as_csv(toc_with_page_end, output_file)
