"""
Functions used for file retrieval.
Script to get files for running accuracy tests.
"""

import os
import glob
import logging
import json
from pathlib import Path

# ----------------- Configure Logging -----------------
logging.basicConfig(
    level=logging.INFO,
    format="[file retrieval] %(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_doc_names(dir, type, keep_prefix=True, prefix_delimiter="_"):
    """
    Return a list of txt document names from `dir` without the .txt extensions.

    If `keep_prefix` is True, return original document names.
    Otherwise, strip prefix names (everything before the final prefix delimiter).
    - For example: gt_kbaa-123.txt -> kbaa-123.txt (prefix_delimiter='_')
    """

    gt_paths = glob.glob(os.path.join(dir, f"*.{type}"))
    logger.info("Found ground-truth txt files: %s", gt_paths)

    doc_names = [os.path.splitext(os.path.basename(p))[0] for p in gt_paths]
    logger.info("Found file names: %s", doc_names)
    logger.info(len(doc_names))

    # Strip prefix names if requested
    if not keep_prefix:
        doc_names = list(
            map(lambda name: str.split(name, prefix_delimiter)[-1], doc_names)
        )
    return doc_names


def get_all_models(type, *argv):
    """
    NOTE: This example is for txt files, for JSON, specify in the type parameter
    llm_root is the directory where LLM model folders are located.
    ocr_root is the directory where OCR model folders are located.
    ocr_llm_root is the directory where OCR-LLM model folders are located.
    type is the format of the document

    Example file structure for txt:
    - llm_root
        - gpt-4o
            - doc1.txt
            - doc2.txt
        - gemini-2.0
            - doc1.txt
            - doc2.txt
    - ocr_root
        - pytesseract
            - doc1.txt
            - doc2.txt

    Returns a list of 2-tuples with
    - the model type:
        - "llm_img2txt" for LLM models
        - "ocr_img2txt" for OCR models
    - the model name (found using the directory structure)
    """
    all_models = []
    for arg in argv:
        if os.path.isdir(arg):
            for model in os.listdir(arg):
                all_models.append((os.path.basename(arg), model))
    # sort by model name
    all_models.sort(key=lambda x: x[1].lower())

    return all_models


def get_docs(dir, doc_names, doc_format, name_has_prefix=False):
    """
    Returns a 2-tuple containing
    - a dict with
        - `doc_names` as the keys
        - The contents of `dir/{doc}` as the corresponding values
        (assuming `doc` is a key of `doc_name`).
            - If `name_has_prefix` is True, `doc` may be preceded by any prefix.
    - a string/json depending on `type` specified, containing the content of all the values in the dict
        - in the order given by doc_names
        - each value is separated by a newline if text else json with "entries" key, list of entries as values

    Since doc_names is a list, all_docs preserves order between different directories.
    """

    docs = {}
    all_docs = "" if doc_format == "txt" else {"entries": []}
    for doc in doc_names:
        doc_pattern = (
            f"*{doc}.{doc_format}" if name_has_prefix else f"{doc}.{doc_format}"
        )
        paths = glob.glob(os.path.join(dir, doc_pattern))
        print(doc)
        with open(paths[0], "r", encoding="utf-8") as f:
            # If data is txt parse it as text else parse as json (separate file reading functions)
            data = f.read()
            if doc_format == "json":
                data = json.loads(data)
        docs[doc] = data
        if doc_format == "txt":
            all_docs += data + "\n"
        elif doc_format == "json":
            # Aggregates all entries into a single array in the json object
            all_docs["entries"] += data["entries"]

    return docs, all_docs


def get_paths(dir, doc_format, name_has_prefix=False):
    # Add all filenames in images directory into the `filenames` array with the ENTIRE filepath
    filepaths = []
    for path in dir.iterdir():
        if path.suffix.lower() == f".{doc_format}" and path.is_file():
            filepaths.append(path)
    return filepaths


"""
all_docs = {
    "entries": [
        {
            "city": "Tokyo..."
            "city": "Tokyo..."
        },
        {
            "food": "sushi",
            "food": "sushi",
        }
        {
            All the other entries throughout the entire book
        },
        ...
    ]
}
"""
