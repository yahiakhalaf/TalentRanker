# TalentRanker

AI-Powered Resume Ranking & Candidate Matching System

## Overview

TalentRanker is an intelligent recruitment tool that automates the process of matching candidates to job descriptions. It uses advanced AI techniques including natural language processing, embedding-based similarity matching, and structured data extraction to rank resumes against job requirements.

## Features

###  Core Capabilities
- **Multi-format Support**: Processes PDFs, DOCX, TXT, MD, PNG, JPG, and JPEG files
- **Dual Processing Modes**: 
  - AI-Enhanced: Uses Docling + LLM for superior accuracy
  - OCR + Embeddings: Faster processing with embedding-based ranking
- **Intelligent Document Conversion**: Automatic OCR for scanned documents
- **Structured Data Extraction**: Extracts comprehensive candidate information using AI
- **Multi-dimensional Scoring**: Evaluates candidates across 11 different criteria
- **Batch Processing**: Handles multiple resumes and job descriptions simultaneously
- **Interactive Web Interface**: User-friendly Gradio-based UI
- **Export Functionality**: CSV export for ranking results

### Scoring Categories
TalentRanker evaluates candidates across these dimensions:

1. **Job Title Relevance** (3%)
2. **Experience Years Match** (20%)
3. **Education Match** (20%)
4. **Experience Relevance** (8%)
5. **Skills Match** (20%)
6. **Soft Skills Relevance** (4%)
7. **Certifications Match** (5%)
8. **Domain Knowledge Match** (4%)
9. **Languages Match** (10%)
10. **Preferred Education Relevance** (3%)
11. **Preferred Qualifications Relevance** (3%)

## Architecture

```
TalentRanker/
├── src/
│   ├── config_loader.py          # Configuration management
│   ├── data_parser.py             # Document-to-markdown conversion
│   ├── resume_extractor.py        # AI-powered resume parsing
│   ├── description_extractor.py   # Job description parsing
│   ├── resumes_ranker.py          # AI-based ranking
│   ├── ui_utils.py                # Pipeline orchestration
│   ├── gradio.py                  # Web interface
│   ├── prompts.py                 # LLM prompts
│   ├── utils.py                   # Data models and utilities
│   └── embed_ranker/
│       ├── embed_ranker.py        # Embedding-based ranking
│       ├── embed_utils.py         # Embedding utilities
│       └── similarity_calculator.py # Similarity calculations
├── config.yaml                    # Main configuration
├── docker-compose.yml             # Docker deployment
├── Dockerfile                     # Container definition
└── pyproject.toml                 # Python dependencies
```

## Installation

### Prerequisites
- Python 3.12+
- Google Gemini API key
- Docker (optional)

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/talentranker.git
   cd talentranker
   ```

2. **Install system dependencies**
   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install tesseract-ocr libtesseract-dev libpng-dev libjpeg-dev

   # macOS
   brew install tesseract

   # Windows
   # Download and install Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
   ```

3. **Install Python dependencies**
   ```bash
   pip install uv
   uv pip install .
   ```

4. **Set up environment variables**
   ```bash
   export GOOGLE_API_KEY="your_gemini_api_key_here"
   ```

5. **Run the application**
   ```bash
   python -m src.gradio
   ```

### Option 2: Docker Installation

1. **Clone and build**
   ```bash
   git clone https://github.com/your-username/talentranker.git
   cd talentranker
   ```

2. **Create environment file**
   ```bash
   echo "GOOGLE_API_KEY=your_gemini_api_key_here" > .env
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   Open your browser to `http://localhost:8765`

## Configuration

The system is configured through `config.yaml`. Key settings include:

### Model Configuration
```yaml
models:
  sentence_transformer: "all-MiniLM-L6-v2"
  language_model:
    model_name: "gemini-2.5-flash"
    temperature: 0
    api_key: "${GOOGLE_API_KEY}"
```

### Scoring Weights
Customize the importance of different evaluation criteria:
```yaml
scoring:
  weights:
    experience_years_match: 0.20
    education_match: 0.20
    skills_match: 0.20
    # ... other weights
```

### Processing Settings
```yaml
processing:
  batch_size: 10  # Number of resumes processed per LLM call

ui:
  interface:
    server:
      host: "0.0.0.0"
      port: 7860
```

## Usage

### Web Interface

1. **Start the application** using one of the installation methods above
2. **Upload files**:
   - Resume files: Upload candidate resumes in supported formats
   - Job description files: Upload job postings or descriptions
3. **Configure processing**:
   - **Enhance ranking with AI**: Use LLM for detailed analysis (slower, more accurate)
   - **Enhance conversion with AI**: Use Docling for document conversion (slower, better quality)
4. **Process & rank**: Click "Process & Rank Candidates"
5. **View results**: Results are displayed in tables grouped by job title
6. **Export data**: Download CSV files for further analysis

### Processing Modes

#### AI-Enhanced Mode
- Uses Google Gemini for structured data extraction
- LLM-based candidate ranking with detailed scoring
- Higher accuracy but slower processing
- Best for detailed analysis and smaller batches

#### OCR + Embeddings Mode  
- Uses OCR for document conversion
- Embedding-based similarity matching
- Faster processing for large volumes
- Good balance of speed and accuracy


## Data Processing Pipeline

1. **File Upload & Storage**: Uploaded files are saved with unique identifiers
2. **Document Conversion**: Files converted to markdown using either:
   - Docling (AI-enhanced, higher quality)
   - PyMuPDF + Tesseract OCR (faster)
3. **Structured Extraction**: AI extracts structured data from documents
4. **Candidate Ranking**: Resumes ranked against job requirements using either:
   - LLM-based detailed analysis
   - Embedding similarity + fuzzy matching
5. **Results Generation**: Ranked results displayed and exportable as CSV

## Project Structure

### Core Components

- **`config_loader.py`**: Manages configuration from YAML file with environment variable expansion
- **`data_parser.py`**: Handles document conversion to markdown with OCR fallback
- **`resume_extractor.py`**: Extracts structured data from resumes using AI
- **`description_extractor.py`**: Extracts job requirements using AI
- **`resumes_ranker.py`**: AI-based candidate ranking and scoring
- **`embed_ranker/`**: Embedding-based ranking alternative
- **`gradio.py`**: Web interface implementation
- **`ui_utils.py`**: Pipeline orchestration and file management

### Data Models

The system uses Pydantic models for structured data:

- **`ResumeData`**: Complete resume information including experience, education, skills
- **`JobRequirementsData`**: Structured job requirements and qualifications
- **`CandidateMatch`**: Candidate scoring and ranking results
- **`JobMatchingResult`**: Complete job matching results

## Supported File Formats

### Input Formats
- **Documents**: PDF, DOCX, TXT, MD
- **Images**: PNG, JPG, JPEG (with OCR)

### Output Formats
- **JSON**: Structured data storage
- **CSV**: Exportable ranking results
- **Markdown**: Intermediate document format
 

## Dependencies

### Core Dependencies
- **Docling**: Advanced document processing
- **LangChain**: LLM integration and prompting
- **Sentence Transformers**: Embedding generation
- **Gradio**: Web interface
- **PyMuPDF**: PDF processing
- **Pytesseract**: OCR capabilities
- **FuzzyWuzzy**: String matching

### AI Models
- **Google Gemini 2.5 Flash**: Primary LLM for extraction and ranking
- **all-MiniLM-L6-v2**: Sentence embeddings for similarity matching


## License

This project is licensed under the MIT License - see the LICENSE file for details.



Built with ❤️ for modern recruitment teams
