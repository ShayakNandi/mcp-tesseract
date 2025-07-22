# Tesseract OCR Server with FastMCP

This project provides a simple yet powerful Tesseract OCR server built using `FastMCP`. It allows you to perform Optical Character Recognition (OCR) on single image files or batch-process entire folders of images. It also includes tools to analyze word frequencies from the OCR output using an SQLite database, as well as comprehensive bibliography processing tools for both text and JSON ground truth data.

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

## Using the Terminal Clients

This project includes several client options for interacting with the Tesseract server:

### Basic Client (Recommended)

The basic client provides a simple chat interface with keyword-based tool detection. The client automatically spawns its own server process, so you don't need to run the server separately:

**Just run the client:**
```bash
cd mcptesseract
python clients/basic_client.py
```

The client will automatically start the Tesseract server and connect to it.

The basic client recognizes these commands:
- `"OCR image image_folder/Bib1.png"` - OCR a single image
- `"batch OCR folder image_folder"` - Batch process a folder
- `"store word frequencies from transcriptions/file.txt"` - Store word frequencies
- `"query word frequency hello"` - Query frequency of a word
- `"process json bibliography"` - Process JSON bibliography data
- `"query json bibliography about healthcare"` - Search bibliography

### Simple Client

A simpler version that uses a basic protocol:

```bash
python clients/simple_client.py
```

### Advanced Terminal Client

For advanced use with full LLM integration (experimental):

```bash
python clients/terminal_client.py
```

**Note**: Make sure your `.env` file contains your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
```

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

### OCR Tools

### `ocr_image_to_text`

Performs OCR on a single image file and saves the transcription to a text file.

-   **`image_path`**: Path to the image file to process.
-   **`output_folder`** (optional): Folder where the transcription file will be saved. Defaults to `transcriptions`.

### `batch_ocr_folder`

Processes all images in a specified folder and saves the transcriptions to text files.

-   **`image_folder`**: Path to the folder containing images.
-   **`output_folder`** (optional): Folder where transcription files will be saved. Defaults to `transcriptions`.

### Word Frequency Analysis Tools

### `store_word_frequencies`

Stores word frequencies from a transcription file into an SQLite database.

-   **`txt_file_path`**: Path to the text file containing the transcription.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.

### `query_word_frequency`

Queries the frequency of a specific word in the SQLite database.

-   **`word`**: The word whose frequency is to be queried.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.

### `get_all_word_frequencies`

Retrieves all word frequencies from the database, sorted by frequency.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.
-   **`limit`** (optional): Maximum number of results to return. Defaults to 20.

### `clear_word_frequencies`

Deletes all word frequencies from the SQLite database.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `word_freq.db`.

### JSON Bibliography Processing Tools

These tools are designed to process structured JSON bibliography data with detailed metadata:

### `process_json_ground_truth`

Processes all JSON files in the specified folder and stores entries in the bibliography database. Automatically creates an optimized database schema for JSON data.

-   **`json_folder`** (optional): Path to the folder containing JSON ground truth files. Defaults to `json_truth`.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `create_json_bibliography_table`

Creates the bibliography table optimized for JSON ground truth data with proper indexes for performance.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `query_json_bibliography`

Query the JSON bibliography database with natural language queries. Searches across all fields including author names, titles, descriptions, publishers, and locations.

-   **`query`**: Natural language query about books, authors, topics, etc.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.
-   **`limit`** (optional): Maximum number of results to return. Defaults to 20.

### `search_by_author`

Search for all works by a specific author (searches both first and last names).

-   **`author_name`**: Name to search for (can be first name, last name, or partial).
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `search_by_year_range`

Search for works published within a specific year range.

-   **`start_year`**: Beginning year of the range.
-   **`end_year`**: End year of the range.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `get_json_bibliography_stats`

Get comprehensive statistics about the JSON bibliography database including author counts, publication year ranges, library distributions, and more.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `display_all_json_bibliography`

Display all entries from the JSON bibliography database in various formats.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.
-   **`format`** (optional): Output format - 'detailed', 'compact', or 'csv'. Defaults to 'compact'.
-   **`limit`** (optional): Maximum number of entries to display. Defaults to 100, use 0 for all.

### `clear_json_bibliography`

Completely clears the bibliography database by dropping the table.

-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### Legacy Bibliography Tools (Text-based)

These tools work with parsed text bibliography entries:

### `process_ground_truth_folder`

Processes text files containing bibliography entries and stores them in a SQLite database.

-   **`folder_path`**: Path to the folder containing ground truth text files. Defaults to `ground_truth`.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `query_bibliography`

Searches for specific entries in the bibliography database using natural language queries.

-   **`query`**: Search terms to look for in the bibliography.
-   **`limit`** (optional): Maximum number of results to return. Defaults to 10.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

### `search_by_topic`

Searches for books and entries related to a specific topic.

-   **`topic`**: Topic to search for (e.g., "healthcare", "fitness", "pioneer").
-   **`limit`** (optional): Maximum number of results to return. Defaults to 15.
-   **`db_path`** (optional): Path to the SQLite database file. Defaults to `bibliography.db`.

## JSON Bibliography Database Schema

The JSON bibliography data is stored in a SQLite database with the following optimized schema:

- `id`: Auto-incrementing primary key
- `lastname`: Author's last name
- `firstname`: Author's first name
- `birthyear`: Author's birth year
- `deathyear`: Author's death year (if applicable)
- `title`: Book or work title
- `city`: Publication city
- `publisher`: Publisher name
- `publishyear`: Publication year
- `pagecount`: Number of pages
- `library`: Library code where the work is held
- `description`: Brief description or notes about the work
- `index_num`: Original index number from source data
- `source_file`: JSON file the entry was imported from
- `created_at`: Timestamp of entry creation

### Database Indexes

The database includes the following indexes for optimal query performance:
- `idx_lastname` on lastname
- `idx_firstname` on firstname  
- `idx_title` on title
- `idx_publishyear` on publishyear
- `idx_library` on library
- `idx_description` on description

## Legacy Bibliography Database Schema

The legacy text-based bibliography data uses this schema:

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

## JSON Data Format

The JSON bibliography files should follow this structure:

```json
{
  "entries": [
    {
      "lastname": "Smith",
      "firstname": "John",
      "birthyear": 1850,
      "deathyear": 1920,
      "title": "My Life Story",
      "city": "New York",
      "publisher": "Random House",
      "publishyear": 1910,
      "pagecount": 256,
      "library": "DLC",
      "description": "Autobiography of a businessman",
      "index": 1
    }
  ]
}
```

All fields are optional except for the `entries` array structure.
