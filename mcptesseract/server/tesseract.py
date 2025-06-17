import os
import glob
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


