# doc2quiz

This project is used to generate quiz questions from a pdf document.
# doc2quiz

This project create a [Canvas](https://canvas.instructure.com/) quiz from pdf by asking Chat API
to create questions.

## Project Organization


The program assumes a directory structure and environment variables to access chat API.
For injesting the initial files, it expects a pdf and csv file, eg:
    [toc.csv](inputs/csv/toc.csv)
    [book.pdf](inputs/pdf/book.pdf)

the `toc.csv` file has the start/end page numbers, a tag to mark each section and a title. eg:
```
start,end,chapter,title
33,38,7.0,7 Cell structure
33,36,7.1,7.1 What is a cell?
37,37,7.2,7.2 History of cell knowledge
```

chapter field is a tag to mark each quiz section, which should be a unique short number or
something like that.
the utility [pdf_extract_toc.py](bin/pdf_extract_toc.py) could be used to produce a good starting
point to edit.  each section should be a couple of pages of text--too much text in one section
would go over the chat session token limits.


## Running doc2quiz

### Step1: injesting the data

In the first phase data is injested into the system by converting pdf chapters marked in toc.csv
into separate pages:
```
    doc2quiz --convert pdf2txt
```

### Step2: asking GPT to make up questions

Quiz questions happen to be stored here in yaml format, so `txt2yaml` converts chapter contents
to yaml. Process relies on having a OPENAI_API_KEY defined in environment.
```
    doc2quiz --convert txt2yaml
```
It's useful to go through the questions at this point and cull or edit questions.


### Step3: Converting questions to Canvas QTI format

Canvas can read in questions using an XML format called QTI. The next step converts from yaml to
qti xml:
```
    doc2quiz --convert yaml2xml
```
You can also convert directly from `pdf2yaml` or `pdf2xml`, which runs all 3 steps in one session.

### Step4: Uploading quiz to Canvas 

At the end of generation, there is an xml directory under output/xml and a zip file called
output/xml.zip that can be uploaded as shown in
(https://community.canvaslms.com/t5/Instructor-Guide/How-do-I-import-quizzes-from-QTI-packages/ta-p/1046)

## Running from cloned dir

to run the program under bin/, you might have to add the src dir to your
python path with:

```
pip install -e .
```


- `bin`: doc2quiz executable
- `src`: main source code doc doc2quiz
- `.github/workflows`: Contains GitHub Actions used for building, testing, and publishing.
- `.devcontainer/Dockerfile`: Contains Dockerfile to build a development container for VSCode 
- `.devcontainer/devcontainer.json`: Contains the configuration for the development container for VSCode, including the Docker image to use, any additional VSCode extensions to install, and whether or not to mount the project directory into the container.
- `.vscode/settings.json`: Contains VSCode settings specific to the project, such as the Python interpreter to use and the maximum line length for auto-formatting.
- `tests`: Contains Python-based test cases to validate source code.
- `pyproject.toml`: Contains metadata about the project and configurations for additional tools used to format, lint, type-check, and analyze Python code.


[Microsoft Python package template](https://github.com/microsoft/python-package-template) was used to create the project.

