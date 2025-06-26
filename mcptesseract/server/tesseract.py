import os
import glob
import sqlite3
import re
import json
from datetime import datetime
from pathlib import Path
from PIL import Image
import pytesseract
from mcp.server.fastmcp import FastMCP


# Create MCP instance
mcp = FastMCP("Tesseract OCR Server")


@mcp.tool()
def ocr_image_to_text(image_path: str, output_folder: str = "transcriptions") -> str:
    """
    Perform OCR on an image file and save the transcription to a text file.
    
    Args:
        image_path: Path to the image file to process
        output_folder: Folder where transcription text files will be saved
    
    Returns:
        Success message with paths of processed files
    """
    try:
        # Validate image file exists
        if not os.path.exists(image_path):
            return f"Error: Image file not found at {image_path}"
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Load and process the image
        image = Image.open(image_path)
        
        # Extract text using pytesseract
        extracted_text = pytesseract.image_to_string(image)
        
        # Generate output filename based on input image name
        image_name = Path(image_path).stem
        output_filename = f"{image_name}_transcription.txt"
        output_path = os.path.join(output_folder, output_filename)
        
        # Save transcription to text file
        with open(output_path, 'w', encoding='utf-8') as text_file:
            text_file.write(extracted_text)
        
        return f"Successfully processed {image_path}. Transcription saved to {output_path}"
        
    except Exception as e:
        return f"Error processing {image_path}: {str(e)}"

@mcp.tool()
def batch_ocr_folder(image_folder: str, output_folder: str = "transcriptions") -> str:
    """
    Process all images in a folder and save transcriptions to text files.
    
    Args:
        image_folder: Path to folder containing images to process
        output_folder: Folder where transcription text files will be saved
    
    Returns:
        Summary of batch processing results
    """
    try:
        # Validate input folder exists
        if not os.path.exists(image_folder):
            return f"Error: Image folder not found at {image_folder}"
        
        # Create output folder if it doesn't exist
        os.makedirs(output_folder, exist_ok=True)
        
        # Supported image extensions
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff', '*.gif']
        
        processed_files = []
        failed_files = []
        
        # Process all images in the folder
        for extension in image_extensions:
            image_files = glob.glob(os.path.join(image_folder, extension))
            image_files.extend(glob.glob(os.path.join(image_folder, extension.upper())))
            
            for image_path in image_files:
                try:
                    # Load and process the image
                    image = Image.open(image_path)
                    
                    # Extract text using pytesseract
                    extracted_text = pytesseract.image_to_string(image)
                    
                    # Generate output filename
                    image_name = Path(image_path).stem
                    output_filename = f"{image_name}_transcription.txt"
                    output_path = os.path.join(output_folder, output_filename)
                    
                    # Save transcription to text file
                    with open(output_path, 'w', encoding='utf-8') as text_file:
                        text_file.write(extracted_text)
                    
                    processed_files.append(output_path)
                    
                except Exception as e:
                    failed_files.append(f"{image_path}: {str(e)}")
        
        # Generate summary report
        summary = f"Batch OCR completed!\n"
        summary += f"Successfully processed: {len(processed_files)} files\n"
        if failed_files:
            summary += f"Failed to process: {len(failed_files)} files\n"
            summary += "Failed files:\n" + "\n".join(failed_files)
        
        return summary
        
    except Exception as e:
        return f"Error during batch processing: {str(e)}"


# Store word frequencies into the database
@mcp.tool()
def store_word_frequencies(txt_file_path: str, db_path: str = "word_freq.db") -> str:
    """
    Stores word frequencies from a transcription file into the SQLite database.
    
    Args:
        txt_file_path: Path to the text file containing the transcription
        db_path: Path to the SQLite database file (default: "word_freq.db")
    
    Returns:
        Success message with the number of words stored
    """
    if not os.path.exists(txt_file_path):
        return f"Error: file not found at {txt_file_path}"

    # Read the transcription file
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        text = f.read().lower()

    # Tokenize the text into words
    words = re.findall(r'\w+', text)

    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create table if it doesn't exist
    cursor.execute("CREATE TABLE IF NOT EXISTS word_freq (word TEXT PRIMARY KEY, count INTEGER)")

    # Insert or update word frequencies
    for word in words:
        cursor.execute("""
            INSERT INTO word_freq (word, count)
            VALUES (?, 1)
            ON CONFLICT(word) DO UPDATE SET count = count + 1
        """, (word,))

    # Commit changes and close the connection
    conn.commit()
    conn.close()

    return f"Stored {len(words)} words from {txt_file_path} into {db_path}"

# Query the frequency of a specific word
@mcp.tool()
def query_word_frequency(word: str, db_path: str = "word_freq.db") -> str:
    """
    Queries the frequency of a word in the SQLite database.
    
    Args:
        word: The word whose frequency is to be queried
        db_path: Path to the SQLite database file (default: "word_freq.db")
    
    Returns:
        A message with the word count, or a not-found message
    """
    # Connect to the SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Query the frequency of the word
    cursor.execute("SELECT count FROM word_freq WHERE word = ?", (word.lower(),))
    row = cursor.fetchone()

    # Close the connection
    conn.close()

    if row:
        return f"'{word}' appears {row[0]} time(s)."
    else:
        return f"'{word}' does not appear in the database."

@mcp.tool()
def get_all_word_frequencies(db_path: str = "word_freq.db", limit: int = 20) -> str:
    """
    Retrieves all word frequencies from the SQLite database, sorted by count.
    
    Args:
        db_path: Path to the SQLite database file (default: "word_freq.db")
        limit: The maximum number of results to return (default: 20)
    
    Returns:
        A string containing the words and their frequencies, or a not-found message.
    """
    if not os.path.exists(db_path):
        return f"Error: Database file not found at {db_path}"

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("SELECT word, count FROM word_freq ORDER BY count DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()

    conn.close()

    if not rows:
        return "The database is empty."

    result = "Word Frequencies:\n"
    result += "-"*20 + "\n"
    for word, count in rows:
        result += f"{word}: {count}\n"
    
    return result

@mcp.tool()
def clear_word_frequencies(db_path: str = "word_freq.db") -> str:
    """
    Deletes all word frequencies from the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file (default: "word_freq.db")
    
    Returns:
        A success or error message.
    """
    if not os.path.exists(db_path):
        return f"Error: Database file not found at {db_path}"

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='word_freq'")
        if cursor.fetchone() is None:
            conn.close()
            return f"Table 'word_freq' does not exist in {db_path}. Nothing to delete."

        cursor.execute("DELETE FROM word_freq")
        conn.commit()
        
        # Vacuum the database to reclaim space
        conn.execute("VACUUM")
        
        conn.close()
        return f"Successfully deleted all word frequencies from {db_path}."
    except sqlite3.Error as e:
        return f"Database error: {e}"
    except Exception as e:
        return f"An error occurred: {e}"


# Bibliography Processing Functions

@mcp.tool()
def create_bibliography_table(db_path: str = "bibliography.db") -> str:
    """
    Creates the bibliography table in the SQLite database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Success or error message
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bibliography (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                author TEXT,
                title TEXT,
                note TEXT,
                year INTEGER,
                place TEXT,
                publisher TEXT,
                pages TEXT,
                library TEXT,
                full_entry TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        return f"Successfully created bibliography table in {db_path}"
    except Exception as e:
        return f"Error creating bibliography table: {str(e)}"


def parse_bibliography_entry(entry_text: str) -> dict:
    """
    Parse a single bibliography entry into structured components.
    
    Args:
        entry_text: Raw text of the bibliography entry
        
    Returns:
        Dictionary with parsed components matching the JSON format
    """
    entry = entry_text.strip()
    if not entry or entry == "Author Entries":
        return None
    
    # Initialize the result dictionary
    result = {
        "author": None,
        "title": None,
        "note": None,
        "year": None,
        "place": None,
        "publisher": None,
        "pages": None,
        "library": None
    }
    
    # Handle cross-reference entries (e.g., "A-No. 1 (pseud.). See Livingston, Leon Ray.")
    if " See " in entry and entry.count('.') <= 2:
        parts = entry.split('. See ')
        if len(parts) == 2:
            result["author"] = parts[0].strip()
            result["note"] = f"See {parts[1]}"
        return result
    
    # Split by periods to identify major components
    parts = entry.split('. ')
    if len(parts) < 2:
        # If no periods, treat entire entry as author
        result["author"] = entry
        return result
    
    # Extract author (first part)
    result["author"] = parts[0].strip()
    
    # Extract library code (usually 2-4 uppercase letters, often at the end)
    library_match = re.search(r'\b([A-Z]{2,4})\b', entry)
    if library_match:
        result["library"] = library_match.group(1)
    
    # Get the last part for notes
    last_part = parts[-1].strip() if len(parts) > 2 else ''
    if len(parts) >= 2:
        # Check if last part looks like a note (doesn't contain publication info)
        if last_part and not re.search(r'\d{4}', last_part) and not ':' in last_part:
            result["note"] = last_part
            # Remove the note part from further processing
            middle_parts = '. '.join(parts[1:-1])
        else:
            middle_parts = '. '.join(parts[1:])
    else:
        middle_parts = ''
    
    if library_match and result["library"] in middle_parts:
        middle_parts = middle_parts.replace(result["library"], '').strip('. ')
    
    # Extract title (everything before publication info)
    title_match = re.match(r'^([^.]+(?:\.\.\.[^.]*)?)', middle_parts)
    if title_match:
        result["title"] = title_match.group(1).strip()
        remaining = middle_parts[len(title_match.group(1)):].strip('. ')
    else:
        remaining = middle_parts
    
    # Extract publication information
    # Look for pattern: Place: Publisher, Year. Pages
    pub_match = re.search(r'([^:]+):\s*([^,]+),\s*(\d{4})\.\s*(\d+\s*p\.)', remaining)
    if pub_match:
        result["place"] = pub_match.group(1).strip()
        result["publisher"] = pub_match.group(2).strip()
        result["year"] = int(pub_match.group(3))
        result["pages"] = pub_match.group(4).strip()
    else:
        # Try to extract year separately
        year_match = re.search(r'\b(\d{4})\b', remaining)
        if year_match:
            result["year"] = int(year_match.group(1))
        
        # Try to extract pages separately
        pages_match = re.search(r'(\d+\s*p\.)', remaining)
        if pages_match:
            result["pages"] = pages_match.group(1)
        
        # Try to extract place and publisher
        place_pub_match = re.search(r'([^:]+):\s*([^,]+)', remaining)
        if place_pub_match:
            result["place"] = place_pub_match.group(1).strip()
            result["publisher"] = place_pub_match.group(2).strip()
    
    return result


@mcp.tool()
def process_ground_truth_folder(folder_path: str = "ground_truth", db_path: str = "bibliography.db") -> str:
    """
    Process all ground truth text files in the specified folder and store entries in the database.
    
    Args:
        folder_path: Path to the folder containing ground truth text files
        db_path: Path to the SQLite database file
        
    Returns:
        Summary of processing results
    """
    try:
        if not os.path.exists(folder_path):
            return f"Error: Ground truth folder not found at {folder_path}"
        
        # Create bibliography table if it doesn't exist
        create_bibliography_table(db_path)
        
        # Get all text files in the folder
        txt_files = glob.glob(os.path.join(folder_path, "*.txt"))
        if not txt_files:
            return f"No text files found in {folder_path}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        total_entries = 0
        processed_files = 0
        failed_entries = 0
        
        for txt_file in txt_files:
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into individual entries (by newlines)
                entries = [line.strip() for line in content.split('\n') if line.strip()]
                
                for entry_text in entries:
                    if entry_text == "Author Entries" or not entry_text:
                        continue
                    
                    parsed_entry = parse_bibliography_entry(entry_text)
                    if parsed_entry:
                        try:
                            cursor.execute("""
                                INSERT INTO bibliography (author, title, note, year, place, publisher, pages, library, full_entry)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                parsed_entry["author"],
                                parsed_entry["title"],
                                parsed_entry["note"],
                                parsed_entry["year"],
                                parsed_entry["place"],
                                parsed_entry["publisher"],
                                parsed_entry["pages"],
                                parsed_entry["library"],
                                entry_text
                            ))
                            total_entries += 1
                        except Exception as e:
                            failed_entries += 1
                            print(f"Failed to insert entry: {entry_text[:50]}... Error: {e}")
                
                processed_files += 1
                
            except Exception as e:
                print(f"Error processing file {txt_file}: {e}")
        
        conn.commit()
        conn.close()
        
        return f"Processing complete!\nFiles processed: {processed_files}\nTotal entries stored: {total_entries}\nFailed entries: {failed_entries}"
        
    except Exception as e:
        return f"Error during ground truth processing: {str(e)}"


@mcp.tool()
def query_bibliography(query: str, db_path: str = "bibliography.db", limit: int = 10) -> str:
    """
    Query the bibliography database with natural language queries.
    
    Args:
        query: Natural language query about books, authors, topics, etc.
        db_path: Path to the SQLite database file
        limit: Maximum number of results to return
        
    Returns:
        Formatted results matching the query
    """
    try:
        if not os.path.exists(db_path):
            return f"Error: Bibliography database not found at {db_path}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Convert query to search terms
        search_terms = query.lower().split()
        
        # Build flexible SQL query
        conditions = []
        params = []
        
        for term in search_terms:
            # Skip common words
            if term in ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'what', 'are', 'about']:
                continue
            
            condition = """(
                LOWER(author) LIKE ? OR 
                LOWER(title) LIKE ? OR 
                LOWER(note) LIKE ? OR 
                LOWER(place) LIKE ? OR 
                LOWER(publisher) LIKE ? OR
                LOWER(full_entry) LIKE ?
            )"""
            conditions.append(condition)
            search_param = f"%{term}%"
            params.extend([search_param] * 6)
        
        if not conditions:
            # If no meaningful search terms, return recent entries
            sql = "SELECT * FROM bibliography ORDER BY created_at DESC LIMIT ?"
            params = [limit]
        else:
            # Combine conditions with OR for broader matching
            sql = f"""
                SELECT * FROM bibliography 
                WHERE {' OR '.join(conditions)}
                ORDER BY created_at DESC 
                LIMIT ?
            """
            params.append(limit)
        
        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return f"No entries found matching your query: '{query}'"
        
        # Format results
        formatted_results = f"Found {len(results)} entries matching '{query}':\n\n"
        
        for i, row in enumerate(results, 1):
            author = row[1] or "Unknown Author"
            title = row[2] or "No Title"
            year = f" ({row[4]})" if row[4] else ""
            place = row[5] or ""
            publisher = row[6] or ""
            note = row[3] or ""
            
            formatted_results += f"{i}. **{author}**{year}\n"
            formatted_results += f"   Title: {title}\n"
            if place and publisher:
                formatted_results += f"   Published: {place}: {publisher}\n"
            elif place or publisher:
                formatted_results += f"   Published: {place or publisher}\n"
            if note:
                formatted_results += f"   Note: {note}\n"
            formatted_results += "\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error querying bibliography: {str(e)}"


@mcp.tool()
def get_bibliography_stats(db_path: str = "bibliography.db") -> str:
    """
    Get statistics about the bibliography database.
    
    Args:
        db_path: Path to the SQLite database file
        
    Returns:
        Statistics about the bibliography entries
    """
    try:
        if not os.path.exists(db_path):
            return f"Error: Bibliography database not found at {db_path}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM bibliography")
        total_count = cursor.fetchone()[0]
        
        # Get entries with years
        cursor.execute("SELECT COUNT(*) FROM bibliography WHERE year IS NOT NULL")
        with_years = cursor.fetchone()[0]
        
        # Get year range
        cursor.execute("SELECT MIN(year), MAX(year) FROM bibliography WHERE year IS NOT NULL")
        year_range = cursor.fetchone()
        
        # Get top authors
        cursor.execute("""
            SELECT author, COUNT(*) as count 
            FROM bibliography 
            WHERE author IS NOT NULL 
            GROUP BY author 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_authors = cursor.fetchall()
        
        # Get top libraries
        cursor.execute("""
            SELECT library, COUNT(*) as count 
            FROM bibliography 
            WHERE library IS NOT NULL 
            GROUP BY library 
            ORDER BY count DESC 
            LIMIT 5
        """)
        top_libraries = cursor.fetchall()
        
        conn.close()
        
        stats = f"Bibliography Database Statistics:\n"
        stats += f"{'='*40}\n"
        stats += f"Total entries: {total_count}\n"
        stats += f"Entries with publication years: {with_years}\n"
        
        if year_range[0] and year_range[1]:
            stats += f"Year range: {year_range[0]} - {year_range[1]}\n"
        
        if top_authors:
            stats += f"\nTop Authors:\n"
            for author, count in top_authors:
                stats += f"  {author}: {count} entries\n"
        
        if top_libraries:
            stats += f"\nTop Libraries:\n"
            for library, count in top_libraries:
                stats += f"  {library}: {count} entries\n"
        
        return stats
        
    except Exception as e:
        return f"Error getting bibliography statistics: {str(e)}"


@mcp.tool()
def search_by_topic(topic: str, db_path: str = "bibliography.db", limit: int = 15) -> str:
    """
    Search for books and entries related to a specific topic.
    
    Args:
        topic: Topic to search for (e.g., "healthcare", "fitness", "pioneer", "California")
        db_path: Path to the SQLite database file
        limit: Maximum number of results to return
        
    Returns:
        Formatted results related to the topic
    """
    try:
        if not os.path.exists(db_path):
            return f"Error: Bibliography database not found at {db_path}"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Search across all text fields for the topic
        search_param = f"%{topic.lower()}%"
        cursor.execute("""
            SELECT author, title, note, year, place, publisher, library, full_entry
            FROM bibliography 
            WHERE LOWER(title) LIKE ? 
               OR LOWER(note) LIKE ? 
               OR LOWER(full_entry) LIKE ?
            ORDER BY 
                CASE 
                    WHEN LOWER(title) LIKE ? THEN 1
                    WHEN LOWER(note) LIKE ? THEN 2
                    ELSE 3
                END,
                year DESC
            LIMIT ?
        """, [search_param, search_param, search_param, search_param, search_param, limit])
        
        results = cursor.fetchall()
        conn.close()
        
        if not results:
            return f"No entries found related to '{topic}'"
        
        formatted_results = f"Found {len(results)} entries related to '{topic}':\n\n"
        
        for i, row in enumerate(results, 1):
            author = row[0] or "Unknown Author"
            title = row[1] or "No Title"
            note = row[2] or ""
            year = f" ({row[3]})" if row[3] else ""
            place = row[4] or ""
            publisher = row[5] or ""
            library = row[6] or ""
            
            formatted_results += f"{i}. **{author}**{year}\n"
            formatted_results += f"   Title: {title}\n"
            if place and publisher:
                formatted_results += f"   Published: {place}: {publisher}\n"
            if library:
                formatted_results += f"   Library: {library}\n"
            if note:
                formatted_results += f"   Note: {note}\n"
            formatted_results += "\n"
        
        return formatted_results
        
    except Exception as e:
        return f"Error searching by topic: {str(e)}"