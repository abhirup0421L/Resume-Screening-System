# parser.py

import PyPDF2
import docx

def read_pdf(file):
    text = ""
    pdf = PyPDF2.PdfReader(file)

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + " "

    return text


def read_docx(file):
    text = ""
    doc = docx.Document(file)

    for para in doc.paragraphs:
        text += para.text + " "

    return text


def read_txt(file):
    return file.read().decode("utf-8")


def extract_text(uploaded_file):

    filename = uploaded_file.name.lower()

    if filename.endswith(".pdf"):
        return read_pdf(uploaded_file)

    elif filename.endswith(".docx"):
        return read_docx(uploaded_file)

    elif filename.endswith(".txt"):
        return read_txt(uploaded_file)

    else:
        return ""