# MCP Tesseract - OCR Server & Benchmarking Framework

A comprehensive Model Context Protocol (MCP) server for Optical Character Recognition (OCR) with integrated benchmarking capabilities for evaluating OCR and multimodal LLM performance.

## 🚀 Project Overview

This project provides:
1. **MCP Tesseract Server** - A fully functional OCR server using Tesseract with word frequency analysis
2. **Benchmarking Framework** - Comprehensive infrastructure for comparing OCR engines and multimodal LLMs
3. **Performance Analysis** - Tools for accuracy measurement and performance evaluation

## 📁 Project Structure

```
mcp-tesseract/
├── benchmarking-results/          # Benchmarking results
│   └── txt-accuracy/             # Image-to-text accuracy metrics
├── config/                       # Configuration files
│   ├── environment.yml          # Conda environment specification
│   └── .env                     # API keys and credentials (template)
├── data/                        # Input data organization
│   ├── tiffs/                   # Input PDFs (type-1.pdf to type-10.pdf)
│   ├── ground-truth/           # Ground truth reference files
│   │   └── txt/                
│   └── pngs/                   # Intermediate image files as PNGs
├── results/                     # Output directory for all models
│   ├── llm-img2csv/            # CSV files from images using multimodal LLMs
│   │   └── <MODEL_NAME>/       # One folder per model
│   ├── llm-txt2csv/            # CSV files from transcribed text using LLMs
│   │   └── <MODEL_NAME>/
│   ├── llm-img2txt/            # Text transcribed from images using multimodal LLMs
│   │   └── <MODEL_NAME>/
│   └── ocr-img2txt/            # Text transcribed from images using OCR software
│       └── <MODEL_NAME>/
├── src/                        # Source code
│   ├── benchmarking/           # Benchmarking tools and analysis
│   ├── llm-img2csv/           # Image to CSV converters using multimodal LLMs
│   ├── llm-txt2csv/           # Text to CSV converters
│   ├── llm-img2txt/           # Image to text converters using multimodal LLMs
│   ├── ocr-img2txt/           # OCR processors
│   └── scripts/               # Utility scripts
├── logs/                       # Log files
└── mcptesseract/              # Original MCP server
    ├── server/
    │   └── tesseract.py       # Main MCP server implementation
    ├── transcriptions/        # OCR output files
    ├── ground_truth/         # Ground truth files for validation
    └── image_folder/         # Input images
```

## 🔧 MCP Tesseract Server

### Current Functionality

The MCP server (`mcptesseract/server/tesseract.py`) provides the following tools:

#### OCR Operations
- **`ocr_image_to_text(image_path, output_folder)`** - Process single image with OCR
- **`batch_ocr_folder(image_folder, output_folder)`** - Batch process all images in a folder

#### Word Frequency Analysis
- **`store_word_frequencies(txt_file_path, db_path)`** - Store word frequencies in SQLite database
- **`query_word_frequency(word, db_path)`** - Query frequency of specific words
- **`get_all_word_frequencies(db_path, limit)`** - Retrieve top word frequencies
- **`clear_word_frequencies(db_path)`** - Clear database

#### OCR-mLLM Pipeline Tools
- **`setup_directories(base_dir)`** - Create complete pipeline directory structure
- **`run_tesseract_pipeline(image_folder, output_folder)`** - Run Tesseract OCR for pipeline
- **`process_with_llm(image_folder, model_name, use_ocr)`** - Process with LLM (direct or OCR+correction)
- **`run_full_pipeline(image_folder, models)`** - Execute complete 3-way comparison pipeline
- **`get_pipeline_status(base_dir)`** - Monitor pipeline status and API key availability
- **`compare_results(base_dir, file_name)`** - Compare results across different methods

### Supported Features
- Multiple image formats: JPG, JPEG, PNG, BMP, TIFF, GIF
- SQLite database for word frequency storage
- Comprehensive error handling
- Batch processing capabilities
- Automatic output directory creation

### Dependencies
- `pytesseract` - Python wrapper for Tesseract OCR
- `PIL (Pillow)` - Image processing
- `sqlite3` - Database operations
- `mcp.server.fastmcp` - MCP server framework

## 🏗️ Benchmarking Framework

### Environment Setup

The project includes a complete Conda environment specification (`config/environment.yml`) with:

#### Core Libraries
- Python 3.11
- Scientific computing: NumPy, Pandas, Matplotlib, Seaborn
- Image processing: Pillow, OpenCV
- Machine learning: scikit-learn

#### OCR Engines
- Tesseract (pytesseract)
- EasyOCR
- PaddleOCR

#### LLM Integration
- OpenAI API client
- Anthropic API client
- Google Generative AI
- Transformers (Hugging Face)
- PyTorch ecosystem

#### Web Framework
- FastAPI
- Uvicorn
- Jinja2 templating

### Configuration

The `.env` template file includes configuration for:
- **API Keys**: OpenAI, Anthropic, Google AI Studio, Azure OpenAI, Hugging Face
- **Database**: SQLite configuration
- **Logging**: Log level and file paths
- **Processing**: Worker threads, batch sizes, timeouts

## 🚀 Getting Started

### 1. Environment Setup

```bash
# Create conda environment
conda env create -f config/environment.yml
conda activate ocr-benchmarking

# Configure API keys
cp config/.env.example config/.env
# Edit config/.env with your actual API keys
```

### 2. Run MCP Server

```bash
cd mcptesseract
python server/tesseract.py
```

### 3. Basic OCR Usage

```python
# Process single image
result = ocr_image_to_text("path/to/image.png", "transcriptions/")

# Batch process folder
result = batch_ocr_folder("image_folder/", "transcriptions/")

# Analyze word frequencies
store_word_frequencies("transcriptions/output.txt", "word_freq.db")
frequencies = get_all_word_frequencies("word_freq.db", limit=20)
```

### 4. OCR-mLLM Pipeline Usage

```python
# Set up pipeline directory structure
setup_directories(".")

# Run complete 3-way comparison pipeline
run_full_pipeline("data/pngs/", "gpt-4o,gemini-2.5-flash")

# Or run individual components:
# 1. OCR processing
run_tesseract_pipeline("data/pngs/")

# 2. Direct LLM transcription
process_with_llm("data/pngs/", "gpt-4o", use_ocr=False)

# 3. OCR + LLM correction
process_with_llm("data/pngs/", "gpt-4o", use_ocr=True)

# Monitor pipeline status
get_pipeline_status(".")

# Compare results
compare_results(".", "image_filename")
```

## 📊 Benchmarking Workflow

### Planned Workflow
1. **Data Preparation**: Place input files in appropriate `data/` subdirectories
2. **Ground Truth Setup**: Prepare reference files in `data/ground-truth/txt/`
3. **OCR Processing**: Run various OCR engines, output to `results/ocr-img2txt/<ENGINE>/`
4. **LLM Processing**: Process with multimodal LLMs, output to respective `results/` folders
5. **Analysis**: Compare results against ground truth using tools in `src/benchmarking/`
6. **Reporting**: Generate accuracy reports in `benchmarking-results/`

### Comparison Targets
- **OCR Engines**: Tesseract, EasyOCR, PaddleOCR
- **Multimodal LLMs**: GPT-4V, Claude 3, Gemini Pro Vision
- **Text Processing**: Various LLM models for structured data extraction

## 🎯 Current Status

### ✅ Completed
- [x] MCP Tesseract server with full OCR functionality
- [x] Word frequency analysis and SQLite integration
- [x] **Complete OCR-mLLM pipeline implementation**
- [x] **LLM integration (OpenAI GPT-4o, Google Gemini)**
- [x] **3-way comparison system (OCR, LLM Direct, OCR+LLM Correction)**
- [x] Comprehensive directory structure for benchmarking
- [x] Conda environment specification with all required dependencies
- [x] Configuration templates for API keys and settings
- [x] Error handling and batch processing capabilities
- [x] **Pipeline orchestration and status monitoring tools**

### 🔄 In Progress
- [ ] Accuracy measurement scripts and metrics computation
- [ ] Statistical analysis implementation
- [ ] Performance comparison utilities
- [ ] Anthropic Claude integration

### 📋 Planned Features
- [ ] Automated benchmarking pipeline with ground truth comparison
- [ ] Performance visualization dashboards
- [ ] Custom evaluation metrics (BLEU, ROUGE, character-level accuracy)
- [ ] Report generation tools
- [ ] Integration with additional OCR engines (EasyOCR, PaddleOCR)
- [ ] Support for more image formats and preprocessing
- [ ] Real-time accuracy monitoring

## 🛠️ Development

### Architecture
- **MCP Server**: FastMCP framework for tool exposure
- **Database**: SQLite for word frequency storage
- **Processing**: Async-capable with configurable concurrency
- **Extensible**: Modular design for adding new OCR engines and LLMs

### Code Quality
- Comprehensive error handling
- Type hints and documentation
- Modular tool-based architecture
- Configurable parameters
- Logging and monitoring ready

## 📝 License

[Add your license here]

## 🤝 Contributing

[Add contribution guidelines here]

## 📞 Contact

[Add contact information here]

---

**Note**: This project combines production-ready OCR capabilities with a robust benchmarking framework for comprehensive evaluation of text extraction and processing technologies. 