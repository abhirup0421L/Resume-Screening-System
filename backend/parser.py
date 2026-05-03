# backend/parser.py (UPGRADED)

import PyPDF2
import docx


def clean_text(text):
    text = text.replace("\n", " ")
    text = text.replace("\t", " ")
    text = " ".join(text.split())
    return text.strip()


def read_pdf(file):
    text = ""

    try:
        pdf = PyPDF2.PdfReader(file)

        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + " "

    except:
        return ""

    return clean_text(text)


def read_docx(file):
    text = ""

    try:
        doc = docx.Document(file)

        for para in doc.paragraphs:
            text += para.text + " "

    except:
        return ""

    return clean_text(text)


def read_txt(file):
    try:
        text = file.read().decode("utf-8")
        return clean_text(text)

    except:
        return ""


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
