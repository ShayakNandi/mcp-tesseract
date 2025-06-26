import os
import glob
import sqlite3
import re
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