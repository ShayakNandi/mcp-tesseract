import os
import glob
import sqlite3
import re
import base64
from pathlib import Path
from PIL import Image
import pytesseract
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create MCP instance
mcp = FastMCP("OCR-mLLM Benchmarking Server")

# Initialize LLM clients (with error handling for missing API keys)
openai_client = None
anthropic_client = None
gemini_client = None

try:
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
except ImportError:
    print("OpenAI library not installed. Install with: pip install openai")

try:
    if os.getenv("ANTHROPIC_API_KEY"):
        from anthropic import Anthropic
        anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
except ImportError:
    print("Anthropic library not installed. Install with: pip install anthropic")

try:
    if os.getenv("GOOGLE_API_KEY"):
        from google import genai
        gemini_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
except ImportError:
    print("Google GenAI library not installed. Install with: pip install google-genai")


# ====================
# ORIGINAL OCR TOOLS
# ====================

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


# ====================
# PIPELINE TOOLS
# ====================

@mcp.tool()
def setup_directories(base_dir: str = ".") -> str:
    """
    Set up the directory structure for the OCR-mLLM pipeline.
    
    Args:
        base_dir: Root directory for the pipeline (default: current directory)
        
    Returns:
        Status message about directory creation
    """
    try:
        root_dir = Path(base_dir)
        
        # Create necessary directories
        dirs_to_create = [
            root_dir / "data" / "pngs",
            root_dir / "data" / "ground-truth" / "txt",
            root_dir / "results" / "ocr-img2txt",
            root_dir / "results" / "llm-img2txt" / "gpt-4o",
            root_dir / "results" / "llm-img2txt" / "gemini-2.5-flash",
            root_dir / "results" / "ocr-llm-img2txt" / "gpt-4o",
            root_dir / "results" / "ocr-llm-img2txt" / "gemini-2.5-flash",
            root_dir / "benchmarking-results" / "txt-accuracy"
        ]
        
        created_dirs = []
        for dir_path in dirs_to_create:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            
        return f"Successfully created pipeline directory structure at {root_dir}:\n" + "\n".join(created_dirs)
        
    except Exception as e:
        return f"Error setting up directories: {str(e)}"

@mcp.tool()
def run_tesseract_pipeline(image_folder: str, output_folder: str | None = None) -> str:
    """
    Run Tesseract OCR on all PNG images in a folder for the pipeline.
    
    Args:
        image_folder: Path to folder containing PNG images
        output_folder: Path to save OCR results (optional, defaults to results/ocr-img2txt)
        
    Returns:
        Summary of OCR processing results
    """
    try:
        source_dir = Path(image_folder)
        if not source_dir.exists():
            return f"Error: Image folder not found at {image_folder}"
        
        if output_folder:
            output_dir = Path(output_folder)
        else:
            # Default to pipeline structure
            if "data/pngs" in str(source_dir):
                base_dir = source_dir.parent.parent
                output_dir = base_dir / "results" / "ocr-img2txt"
            else:
                output_dir = source_dir.parent / "results" / "ocr-img2txt"
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Process all PNG files
        png_files = list(source_dir.glob("*.png"))
        processed_files = []
        failed_files = []
        
        for png_file in png_files:
            try:
                # Extract text using Tesseract
                image = Image.open(png_file)
                extracted_text = pytesseract.image_to_string(image)
                
                # Save result (no _transcription suffix for pipeline)
                output_file = output_dir / f"{png_file.stem}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_text)
                
                processed_files.append(str(output_file))
                
            except Exception as e:
                failed_files.append(f"{png_file}: {str(e)}")
        
        summary = f"Pipeline OCR processing completed!\n"
        summary += f"Successfully processed: {len(processed_files)} files\n"
        summary += f"Output directory: {output_dir}\n"
        if failed_files:
            summary += f"Failed to process: {len(failed_files)} files\n"
            summary += "Failed files:\n" + "\n".join(failed_files)
        
        return summary
        
    except Exception as e:
        return f"Error during pipeline OCR processing: {str(e)}"

@mcp.tool()
def process_with_llm(image_folder: str, model_name: str, use_ocr: bool = False) -> str:
    """
    Process images using LLM (GPT-4o or Gemini) with optional OCR input.
    
    Args:
        image_folder: Path to folder containing images
        model_name: Model to use ('gpt-4o' or 'gemini-2.5-flash')
        use_ocr: Whether to include OCR text in the prompt
        
    Returns:
        Summary of LLM processing results
    """
    try:
        source_dir = Path(image_folder)
        if not source_dir.exists():
            return f"Error: Image folder not found at {image_folder}"
        
        # Check if LLM client is available
        if model_name == "gpt-4o" and not openai_client:
            return "Error: OpenAI client not initialized. Check your OPENAI_API_KEY."
        elif model_name == "gemini-2.5-flash" and not gemini_client:
            return "Error: Gemini client not initialized. Check your GOOGLE_API_KEY."
        elif model_name not in ["gpt-4o", "gemini-2.5-flash"]:
            return f"Error: Unsupported model {model_name}. Supported: gpt-4o, gemini-2.5-flash"
        
        # Set up output directory
        if "data/pngs" in str(source_dir):
            base_dir = source_dir.parent.parent
        else:
            base_dir = source_dir.parent
            
        if use_ocr:
            output_dir = base_dir / "results" / "ocr-llm-img2txt" / model_name
        else:
            output_dir = base_dir / "results" / "llm-img2txt" / model_name
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Define prompts
        prompt_template_ocr_llm = """
You are a text correction assistant. Your task is to clean up and correct errors from raw OCR output.
The text may contain misrecognized characters, broken words, or incorrect formatting.
Carefully read the provided OCR output and produce a corrected version that is grammatically accurate 
and as faithful to the original content as possible. Because this is a historical document, try to 
preserve archaic spelling or formatting where clearly intended. Only correct obvious OCR errors.
Put the dates associated with each entry at the end of the line.

Input (Raw OCR Text):
{input}
"""
        
        prompt_llm = """
You are an expert historian. Your task is to transcribe the provided image into text. The image
is a 20th century bibliographic entry. Because this is a historical document, try to preserve 
archaic spelling or formatting where clearly intended. Put the indices associated with each entry at the end of the line.
Return the text only, nothing else.
"""
        
        # Process images
        png_files = list(source_dir.glob("*.png"))
        processed_files = []
        failed_files = []
        
        for png_file in png_files:
            try:
                # Prepare prompt
                if use_ocr:
                    # Read OCR output
                    ocr_file = base_dir / "results" / "ocr-img2txt" / f"{png_file.stem}.txt"
                    if ocr_file.exists():
                        with open(ocr_file, 'r', encoding='utf-8') as f:
                            ocr_text = f.read()
                        prompt = prompt_template_ocr_llm.format(input=ocr_text)
                    else:
                        failed_files.append(f"{png_file}: OCR file not found at {ocr_file}")
                        continue
                else:
                    prompt = prompt_llm
                
                # Call appropriate LLM
                result_text = ""
                if model_name == "gpt-4o" and openai_client:
                    # Encode image
                    with open(png_file, "rb") as image_file:
                        base64_image = base64.b64encode(image_file.read()).decode('utf-8')
                    
                    response = openai_client.chat.completions.create(
                        model='gpt-4o',
                        messages=[{
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
                            ]
                        }]
                    )
                    result_text = response.choices[0].message.content or ""
                    
                elif model_name == "gemini-2.5-flash" and gemini_client:
                    uploaded_file = gemini_client.files.upload(file=str(png_file))
                    if uploaded_file:
                        response = gemini_client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=[prompt, uploaded_file]
                        )
                        result_text = response.text or ""
                    else:
                        failed_files.append(f"{png_file}: Failed to upload to Gemini")
                        continue
                
                # Save result
                output_file = output_dir / f"{png_file.stem}.txt"
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(result_text)
                
                processed_files.append(str(output_file))
                
            except Exception as e:
                failed_files.append(f"{png_file}: {str(e)}")
        
        summary = f"LLM processing completed with {model_name}!\n"
        summary += f"Mode: {'OCR + LLM correction' if use_ocr else 'Direct LLM transcription'}\n"
        summary += f"Successfully processed: {len(processed_files)} files\n"
        summary += f"Output directory: {output_dir}\n"
        if failed_files:
            summary += f"Failed to process: {len(failed_files)} files\n"
            summary += "Failed files:\n" + "\n".join(failed_files)
        
        return summary
        
    except Exception as e:
        return f"Error during LLM processing: {str(e)}"

@mcp.tool()
def run_full_pipeline(image_folder: str, models: str = "gpt-4o,gemini-2.5-flash") -> str:
    """
    Run the complete OCR-mLLM pipeline on all images.
    
    Args:
        image_folder: Path to folder containing PNG images
        models: Comma-separated list of models to use (default: "gpt-4o,gemini-2.5-flash")
        
    Returns:
        Summary of complete pipeline execution
    """
    try:
        model_list = [m.strip() for m in models.split(",")]
        
        # Step 1: Run Tesseract OCR
        ocr_result = run_tesseract_pipeline(image_folder)
        
        results = [f"=== TESSERACT OCR ===", ocr_result, ""]
        
        # Step 2: Run LLM processing for each model
        for model in model_list:
            # Direct LLM transcription
            llm_result = process_with_llm(image_folder, model, use_ocr=False)
            results.extend([f"=== {model.upper()} DIRECT ===", llm_result, ""])
            
            # OCR + LLM correction
            ocr_llm_result = process_with_llm(image_folder, model, use_ocr=True)
            results.extend([f"=== {model.upper()} + OCR CORRECTION ===", ocr_llm_result, ""])
        
        return "\n".join(results)
        
    except Exception as e:
        return f"Error during full pipeline execution: {str(e)}"

@mcp.tool()
def get_pipeline_status(base_dir: str = ".") -> str:
    """
    Get the current status of the OCR-mLLM pipeline.
    
    Args:
        base_dir: Root directory of the pipeline (default: current directory)
        
    Returns:
        Status report of the pipeline
    """
    try:
        root_dir = Path(base_dir)
        
        status = "OCR-mLLM Pipeline Status:\n"
        status += "=" * 40 + "\n"
        
        # Check input images
        images_dir = root_dir / "data" / "pngs"
        if images_dir.exists():
            png_count = len(list(images_dir.glob("*.png")))
            status += f"Input images: {png_count} PNG files\n"
        else:
            status += "Input images: Directory not found\n"
        
        # Check ground truth
        gt_dir = root_dir / "data" / "ground-truth" / "txt"
        if gt_dir.exists():
            gt_count = len(list(gt_dir.glob("*.txt")))
            status += f"Ground truth files: {gt_count} TXT files\n"
        else:
            status += "Ground truth files: Directory not found\n"
        
        # Check OCR results
        ocr_dir = root_dir / "results" / "ocr-img2txt"
        if ocr_dir.exists():
            ocr_count = len(list(ocr_dir.glob("*.txt")))
            status += f"OCR results: {ocr_count} files\n"
        else:
            status += "OCR results: Directory not found\n"
        
        # Check LLM results
        llm_dirs = [
            ("llm-img2txt", "Direct LLM"),
            ("ocr-llm-img2txt", "OCR+LLM")
        ]
        
        for dir_name, display_name in llm_dirs:
            llm_base_dir = root_dir / "results" / dir_name
            if llm_base_dir.exists():
                status += f"\n{display_name} results:\n"
                for model_dir in llm_base_dir.iterdir():
                    if model_dir.is_dir():
                        count = len(list(model_dir.glob("*.txt")))
                        status += f"  {model_dir.name}: {count} files\n"
            else:
                status += f"{display_name} results: Directory not found\n"
        
        # Check API key availability
        status += "\nAPI Keys Status:\n"
        status += f"OpenAI: {'✓' if openai_client else '✗'}\n"
        status += f"Anthropic: {'✓' if anthropic_client else '✗'}\n"
        status += f"Google/Gemini: {'✓' if gemini_client else '✗'}\n"
        
        return status
        
    except Exception as e:
        return f"Error getting pipeline status: {str(e)}"

@mcp.tool()
def compare_results(base_dir: str = ".", file_name: str | None = None) -> str:
    """
    Compare results from different methods for a specific file or all files.
    
    Args:
        base_dir: Root directory of the pipeline
        file_name: Specific file to compare (without extension), or None for summary
        
    Returns:
        Comparison report
    """
    try:
        root_dir = Path(base_dir)
        
        # Define result directories
        result_dirs = {
            "OCR": root_dir / "results" / "ocr-img2txt",
            "GPT-4o Direct": root_dir / "results" / "llm-img2txt" / "gpt-4o",
            "GPT-4o + OCR": root_dir / "results" / "ocr-llm-img2txt" / "gpt-4o",
            "Gemini Direct": root_dir / "results" / "llm-img2txt" / "gemini-2.5-flash",
            "Gemini + OCR": root_dir / "results" / "ocr-llm-img2txt" / "gemini-2.5-flash"
        }
        
        if file_name:
            # Compare specific file
            comparison = f"Comparison for {file_name}:\n"
            comparison += "=" * 50 + "\n\n"
            
            for method, dir_path in result_dirs.items():
                file_path = dir_path / f"{file_name}.txt"
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    word_count = len(content.split())
                    char_count = len(content)
                    comparison += f"{method}:\n"
                    comparison += f"  Words: {word_count}, Characters: {char_count}\n"
                    comparison += f"  Preview: {content[:100]}...\n\n"
                else:
                    comparison += f"{method}: File not found\n\n"
        else:
            # Summary comparison
            comparison = "Results Summary:\n"
            comparison += "=" * 30 + "\n"
            
            for method, dir_path in result_dirs.items():
                if dir_path.exists():
                    file_count = len(list(dir_path.glob("*.txt")))
                    comparison += f"{method}: {file_count} files\n"
                else:
                    comparison += f"{method}: Directory not found\n"
        
        return comparison
        
    except Exception as e:
        return f"Error comparing results: {str(e)}"