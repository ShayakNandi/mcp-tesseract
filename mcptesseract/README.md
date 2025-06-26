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

3.  **Activate the virtual environment:**
    Once the dependencies are installed, activate the virtual environment.

    -   **On Windows:**
        ```powershell
        .venv\Scripts\activate
        ```
    -   **On macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

## Running the Server

To start the OCR server, run the following command from the `mcptesseract` directory:

```bash
uv run mcp dev server/tesseract.py
```

The server will start, and you can interact with it through the web interface that `mcp` provides, or by using it as a library.

## Using with MCP Inspector

When using the MCP Inspector to interact with the tools, you may need to provide a proxy session token. In the MCP Inspector interface, go to "Configurations" and enter your token in the designated field to authorize access.

## Connecting from Claude Desktop

You can also interact with the OCR server using Claude Desktop as a client. This requires configuring Claude Desktop to connect to the running Tesseract OCR server.

### Troubleshooting `config.claude`

If you encounter issues connecting from Claude Desktop, check your `config.claude` file for the following:

-   **Server Address**: Ensure the server URL is correctly pointing to your running `mcp` server instance. By default, this is often `http://localhost:8000`, but your port may vary.
    
    ```
    # Example configuration
    server_url = "http://localhost:8000"
    ```

-   **Authentication Token**: If you have authentication enabled on your server, ensure you have provided the correct token in your configuration. This is similar to the proxy session token used for the MCP Inspector.
    
    ```
    # Example configuration
    auth_token = "your-secret-token"
    ```

Make sure the server is running before you attempt to connect from the client. If you continue to experience issues, check the server logs for any error messages.

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

### `clear_word_frequencies`

Deletes all word frequencies from the SQLite database.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.

### Bibliography Processing Tools

The server also includes tools for processing and managing bibliographic data:

### `process_ground_truth_folder`

Processes text files containing bibliography entries and stores them in a SQLite database.

-   **`folder_path`**: Path to the folder containing ground truth text files. Defaults to `ground_truth`.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `display_all_bibliography_entries`

Displays all entries in the bibliography database in either compact or detailed format.

-   **`format`**: Display format - either 'compact' (author, year, title, library code) or 'detailed' (all fields).
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `query_bibliography`

Searches for specific entries in the bibliography database using natural language queries.

-   **`query`**: Search terms to look for in the bibliography.
-   **`limit`** (optional): Maximum number of results to return. Defaults to 10.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `get_bibliography_stats`

Retrieves statistics about the bibliography database, including total entries, year ranges, top authors, and libraries.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `search_by_topic`

Searches for books and entries related to a specific topic.

-   **`topic`**: Topic to search for (e.g., "healthcare", "fitness", "pioneer").
-   **`limit`** (optional): Maximum number of results to return. Defaults to 15.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `clear_bibliography`

Deletes all entries from the bibliography database.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

## Bibliography Database Schema

The bibliography data is stored in a SQLite database with the following fields:

- `id`: Auto-incrementing primary key
- `author`: Author name
- `title`: Book or work title
- `note`: Additional notes or comments
- `year`: Publication year
- `place`: Publication place
- `publisher`: Publisher name
- `pages`: Page count or range
- `library`: Library code
- `full_entry`: Complete original entry text
- `created_at`: Timestamp of entry creation
