import json
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pandas as pd

from src.data_parser import convert_files_to_markdown, convert_files_to_markdown_with_ocr
from src.resume_extractor import process_resumes_directory
from src.description_extractor import process_job_descriptions_directory
from src.resumes_ranker import rank_job_descriptions
from src.embed_ranker.embed_ranker import rank_job_descriptions_with_embeddings
from src.config_loader import config

resumes_config=config["data"]["directories"]["resumes"]
job_config=config["data"]["directories"]["job_descriptions"]

def save_uploaded_files(files: List[Any], file_type: str) -> List[str]:
    """
    Save uploaded files with unique identifiers.
    
    Args:
        files: List of uploaded files from Gradio
        file_type: Either 'resumes' or 'job_descriptions'
    
    Returns:
        List of saved file paths
    """
    if not files:
        return []
    
    saved_files = []
    raw_dir_str = config["data"]["directories"][file_type]["raw"]
    raw_dir = Path(raw_dir_str)  
    raw_dir.mkdir(parents=True, exist_ok=True)

    for file in files:
        # Generate unique identifier
        unique_id = str(uuid.uuid4())[:8]
        
        original_name = Path(file.name).name
        file_ext = Path(file.name).suffix
        
        new_filename = f"{unique_id}_{original_name}"
        save_path = Path(raw_dir) / new_filename
        
        # Copy file to destination
        shutil.copy2(file.name, save_path)
        saved_files.append(str(save_path))
        
    return saved_files


def find_original_raw_file(processed_filename: str) -> str:
    """
    Find the original raw file path based on the processed filename.
    
    Args:
        processed_filename: Name of the processed file (e.g., 'resume.md')
    
    Returns:
        Path to the original raw file or empty string if not found
    """
    
    try:
        raw_resumes_dir = Path(config["data"]["directories"]["resumes"]["raw"])
        
        # Remove extension from processed filename to match with raw files
        base_name = Path(processed_filename).stem
        
        # Find file that contains the base name (accounting for unique prefix)
        for raw_file in raw_resumes_dir.iterdir():
            if raw_file.is_file() and base_name in raw_file.stem:
                return str(raw_file)
        
        return ""
        
    except Exception as e:
        print(f"Error finding raw file for {processed_filename}: {e}")
        return ""


def generate_results_dataframes_by_job() -> Dict[str, pd.DataFrame]:
    """
    Generate separate pandas DataFrames and file mappings for each job description.
    
    Returns:
        Dictionary with job titles as keys and nested dictionaries as values
    """
    rankings_dir = Path(config["data"]["directories"]["rankings"])
    job_results = {}
    
    # Load all ranking result files
    for ranking_file in rankings_dir.glob("*.json"):
        try:
            with open(ranking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            job_title = data.get('job_title', 'Unknown')
            candidates_data = []
            
            # Process each candidate
            for candidate in data.get('candidates', {}).get('candidates', []):
                raw_file_path = find_original_raw_file(candidate.get('file_name', ''))
                
                candidate_name = candidate.get('name', 'Unknown') 
                
                candidate_row = {
                    'Candidate Name': candidate_name,
                    'Current Job Title': candidate.get('job_title', ''),
                    'Phone': candidate.get('contact', {}).get('phone', ''),
                    'Email': candidate.get('contact', {}).get('email', ''),
                    'LinkedIn': candidate.get('contact', {}).get('linkedin', ''),
                    'Overall Score': round(candidate.get('overall_score', 0), 2),
                    'Resume File': raw_file_path or candidate.get('file_name', 'Unknown')
                }
                candidates_data.append(candidate_row)
                            
            # Create DataFrame for this job and sort by overall score
            if candidates_data:
                df = pd.DataFrame(candidates_data)
                df = df.sort_values('Overall Score', ascending=False)
                # Add rank column based on sorted order
                df['Rank'] = range(1, len(df) + 1)

                # Reorder columns to put Rank first
                columns = ['Rank'] + [col for col in df.columns if col != 'Rank']
                df = df[columns]
                job_results[job_title] = df

        except Exception as e:
            print(f"Error processing ranking file {ranking_file}: {e}")
            continue
    
    return job_results


def process_files_pipeline_ai_enhanced(resume_files: List[Any], jd_files: List[Any], llm, enhance_conversion: bool = True) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    AI-enhanced pipeline using docling and AI extraction/ranking.
    
    Args:
        resume_files: List of uploaded resume files
        jd_files: List of uploaded job description files
        llm: Language model instance
    
    Returns:
        Tuple of (status_message, dict of {job_title: dataframe})
    """
    try:        
        # Save uploaded files
        print("Saving uploaded files...")
        saved_resumes = save_uploaded_files(resume_files, "resumes")
        saved_jds = save_uploaded_files(jd_files, "job_descriptions")
        
        if not saved_resumes or not saved_jds:
            return "Error: Please upload both resume and job description files.", {}
        
        print(f"Saved {len(saved_resumes)} resumes and {len(saved_jds)} job descriptions\n")
        
        # Replace the conversion section in both functions with:
        if enhance_conversion:
            print("Converting files to markdown with AI (Docling)...")
            convert_files_to_markdown(resumes_config["raw"],  resumes_config["sub"], "markdown")
            convert_files_to_markdown(job_config["raw"], job_config["sub"], "markdown")
        else:
            print("Converting files to markdown with OCR...")
            convert_files_to_markdown_with_ocr(resumes_config["raw"],  resumes_config["sub"], "markdown")
            convert_files_to_markdown_with_ocr(job_config["raw"], job_config["sub"], "markdown")
        # Extract structured data from resumes using AI
        print("\nExtracting resume data with AI...")
        process_resumes_directory(resumes_config["markdown"],resumes_config["json"], llm)
        
        # Extract structured data from job descriptions using AI
        print("\nExtracting job description data with AI...")
        process_job_descriptions_directory(job_config["markdown"],job_config["json"], llm)
        
        # Rank resumes against job descriptions using AI
        print("\nRanking candidates with AI...")
        rank_job_descriptions(resumes_config["json"], 
                              job_config["json"], llm, 
                              config["data"]["directories"]["rankings"],batch_size=config["processing"]["batch_size"])
        
        # Generate results dataframes grouped by job description
        results_dfs = generate_results_dataframes_by_job()
        
        return "Processing completed successfully with AI enhancement!", results_dfs
        
    except Exception as e:
        return f"Error during AI-enhanced processing: {str(e)}", {}


def process_files_pipeline_ocr_embedding(resume_files: List[Any], jd_files: List[Any], llm, enhance_conversion: bool = True) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    OCR + embedding-based pipeline for faster processing.
    
    Args:
        resume_files: List of uploaded resume files
        jd_files: List of uploaded job description files
        llm: Language model instance (used minimally)
    
    Returns:
        Tuple of (status_message, dict of {job_title: dataframe})
    """
    try:        
        # Save uploaded files
        print("Saving uploaded files...")
        saved_resumes = save_uploaded_files(resume_files, "resumes")
        saved_jds = save_uploaded_files(jd_files, "job_descriptions")
        
        if not saved_resumes or not saved_jds:
            return "Error: Please upload both resume and job description files.", {}
        
        print(f"Saved {len(saved_resumes)} resumes and {len(saved_jds)} job descriptions\n")
        
        # Replace the conversion section in both functions with:
        if enhance_conversion:
            print("Converting files to markdown with AI (Docling)...")
            convert_files_to_markdown(resumes_config["raw"],  resumes_config["sub"], "markdown")
            convert_files_to_markdown(job_config["raw"], job_config["sub"], "markdown")
        else:
            print("Converting files to markdown with OCR...")
            convert_files_to_markdown_with_ocr(resumes_config["raw"],  resumes_config["sub"], "markdown")
            convert_files_to_markdown_with_ocr(job_config["raw"], job_config["sub"], "markdown")
        # Extract structured data from resumes using AI (still needed for structured extraction)
        print("\nExtracting resume data...")
        process_resumes_directory(config["data"]["directories"]["resumes"]["markdown"],resumes_config["json"], llm)
        
        # Extract structured data from job descriptions using AI (still needed for structured extraction)
        print("\nExtracting job description data...")
        process_job_descriptions_directory(job_config["markdown"],job_config["json"], llm)
        
        # Rank resumes using embedding-based approach
        print("\nRanking candidates with embeddings...")
        rank_job_descriptions_with_embeddings(resumes_config["json"], 
                                              job_config["json"], 
                                              config["data"]["directories"]["rankings"])
        
        # Generate results dataframes grouped by job description
        results_dfs = generate_results_dataframes_by_job()
        
        return "Processing completed successfully with OCR + embedding-based ranking!", results_dfs
        
    except Exception as e:
        return f"Error during OCR + embedding processing: {str(e)}", {}


def process_files_pipeline(resume_files: List[Any], jd_files: List[Any], llm, enhance_with_ai: bool = True, enhance_conversion: bool = True) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Complete pipeline to process uploaded files and return results grouped by job description.
    Routes to either AI-enhanced or OCR+embedding processing based on user selection.
    
    Args:
        resume_files: List of uploaded resume files
        jd_files: List of uploaded job description files
        llm: Language model instance
        enhance_with_ai: Boolean flag to determine processing method
    
    Returns:
        Tuple of (status_message, dict of {job_title: dataframe})
    """
    if enhance_with_ai:
        return process_files_pipeline_ai_enhanced(resume_files, jd_files, llm, enhance_conversion)
    else:
        return process_files_pipeline_ocr_embedding(resume_files, jd_files, llm, enhance_conversion)

def save_dataframe_to_csv(job_title: str, job_results: Dict[str, pd.DataFrame]) -> str:
    """
    Save a specific job's DataFrame to CSV file.
    
    Args:
        job_title (str): The job title to save
        job_results (Dict): Dictionary containing job results
    
    Returns:
        str: Status message
    """
    try:
        # Create exports directory if it doesn't exist
        exports_dir = Path(config["data"]["directories"]["exports"])
        exports_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the DataFrame for the specific job
        if job_title not in job_results:
            return f"Job '{job_title}' not found in results."
        
        df = job_results[job_title]
        
        # Create filename (sanitize job title for filename)
        safe_job_title = "".join(c for c in job_title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        filename = f"{safe_job_title.replace(' ', '_')}_candidates.csv"
        filepath = exports_dir / filename
        
        # Save DataFrame to CSV
        df.to_csv(filepath, index=False, encoding='utf-8')
        
        return f"Successfully saved '{job_title}' results to: {filepath}"
        
    except Exception as e:
        return f"Error saving CSV for '{job_title}': {str(e)}"