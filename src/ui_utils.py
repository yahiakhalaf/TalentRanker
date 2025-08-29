import json
import shutil
import uuid
from pathlib import Path
from typing import List, Tuple, Dict, Any
import pandas as pd

from src.data_parser import convert_files_to_markdown
from src.resume_extractor import process_resumes_directory
from src.description_extractor import process_job_descriptions_directory
from src.resumes_ranker import rank_job_descriptions



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
    raw_dir = Path(f"data/{file_type}/raw")    
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
        raw_resumes_dir = Path("data/resumes/raw")
        
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
    rankings_dir = Path("data/rankings")
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

                job_results[job_title] = df

        except Exception as e:
            print(f"Error processing ranking file {ranking_file}: {e}")
            continue
    
    return job_results



def process_files_pipeline(resume_files: List[Any], jd_files: List[Any], llm) -> Tuple[str, Dict[str, pd.DataFrame]]:
    """
    Complete pipeline to process uploaded files and return results grouped by job description.
    
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
        
        # Convert files to markdown
        print("Converting files to markdown...")
        convert_files_to_markdown("data/resumes/raw", "data/resumes", "markdown")
        convert_files_to_markdown("data/job_descriptions/raw", "data/job_descriptions", "markdown")
        
        # Extract structured data from resumes
        print("\nExtracting resume data...")
        process_resumes_directory("data/resumes/markdown", "data/resumes/json", llm)
        
        # Extract structured data from job descriptions
        print("\nExtracting job description data...")
        process_job_descriptions_directory("data/job_descriptions/markdown", "data/job_descriptions/json", llm)
        
        # Rank resumes against job descriptions
        print("\nRanking candidates...")
        rank_job_descriptions("data/resumes/json", "data/job_descriptions/json", llm, "data/rankings")
        
        # Generate results dataframes grouped by job description
        results_dfs = generate_results_dataframes_by_job()
        
        return "Processing completed successfully!", results_dfs
        
    except Exception as e:
        return f"Error during processing: {str(e)}", {}


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
        exports_dir = Path("data/exports")
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
