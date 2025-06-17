# Tesseract OCR Server with FastMCP

This project provides a simple yet powerful Tesseract OCR server built using `FastMCP`. It allows you to perform Optical Character Recognition (OCR) on single image files or batch-process entire folders of images. It also includes tools to analyze word frequencies from the OCR output using an SQLite database.

## Prerequisites

Before you can run this server, you need to have the following installed on your system:

1.  **Python 3.11+**
2.  **Git**
3.  **Tesseract OCR Engine**: `pytesseract` is a Python wrapper for the Tesseract-OCR Engine. You must install Tesseract separately. You can find installation instructions for your OS here:
    - [Tesseract at UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd mcp-tesseract/mcptesseract
    ```

2.  **Install Python dependencies:**
    This project uses `uv` for package management. You can install the required packages by running:
    ```bash
    pip install uv
    uv sync
    ```

## Running the Server

To start the OCR server, run the following command from the `mcptesseract` directory:

```bash
uv run mcp dev server/tesseract.py
```

The server will start, and you can interact with it through the web interface that `mcp` provides, or by using it as a library.

## Using with MCP Inspector

When using the MCP Inspector to interact with the tools, you may need to provide a proxy session token. In the MCP Inspector interface, go to "Configurations" and enter your token in the designated field to authorize access.

## Available Tools

### `ocr_image_to_text`

Performs OCR on a single image file and saves the transcription to a text file.

-   **`image_path`**: Path to the image file to process.
-   **`output_folder`** (optional): Folder where the transcription file will be saved. Defaults to `transcriptions`.

### `batch_ocr_folder`

Processes all images in a specified folder and saves the transcriptions to text files.

-   **`image_folder`**: Path to the folder containing images.
-   **`output_folder`** (optional): Folder where transcription files will be saved. Defaults to `transcriptions`.

### `store_word_frequencies`

Stores word frequencies from a transcription file into an SQLite database.

-   **`txt_file_path`**: Path to the text file containing the transcription.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.

### `query_word_frequency`

Queries the frequency of a specific word in the SQLite database.

-   **`word`**: The word whose frequency is to be queried.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.
