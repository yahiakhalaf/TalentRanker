import json
from pathlib import Path
from typing import Dict, List, Optional
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from src.utils import JobRequirementsData,default_job_requirements
from src.prompts import JOB_DESCRIPTION_EXTRACTION_PROMPT


def process_job_description_file(jd_file: Path, llm: BaseLanguageModel) -> Dict:
    """
    Process a single job description file and extract structured data.

    Args:
        jd_file (Path): Path to the job description file.
        llm (BaseLanguageModel): The language model instance for processing.

    Returns:
        Dict: Extracted job description data as a dictionary.
    """
    try:
        with open(jd_file, 'r', encoding='utf-8') as f:
            jd_text = f.read()

        print(f"Processing job description from: {jd_file.name}")

        prompt = PromptTemplate(
            template=JOB_DESCRIPTION_EXTRACTION_PROMPT,
            input_variables=["job_description_text"]
        )
        
        # Configure the LLM for structured output based on the Pydantic model
        structured_llm = llm.with_structured_output(JobRequirementsData)
        chain = prompt | structured_llm
        
        jd_data = chain.invoke({"job_description_text": jd_text})
        
        result = jd_data.dict()
        result['filename'] = jd_file.name
        
        return result
    
    except Exception as e:
        print(f"Error processing job description from {jd_file.name}: {str(e)}")
        # Return a default
        result = default_job_requirements.dict()
        result['filename'] = jd_file.name
        return result

def process_job_descriptions_directory(jds_dir: str, output_dir: str, llm: BaseLanguageModel) -> None:
    """
    Process all job description files in a directory and save each as a separate JSON file.

    Args:
        jds_dir (str): Directory containing job description files.
        output_dir (str): Directory to save processed JSON files.
        llm (BaseLanguageModel): The language model instance for processing.

    Returns:
        None
        
    Raises:
        FileNotFoundError: If the input directory does not exist.
    """
    jds_path = Path(jds_dir)
    if not jds_path.exists():
        raise FileNotFoundError(f"Directory {jds_dir} does not exist")
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all text files 
    jd_files = list(jds_path.glob("*.md"))
    total_files = len(jd_files)
    
    if total_files == 0:
        print("No job description files found in the directory.")
        return
    
    print(f"Found {total_files} job description files to process.")
    print(f"Output will be saved to: {output_dir}")
    
    for jd_file in jd_files:
        try:
            jd_data = process_job_description_file(jd_file, llm)
            
            output_file = output_path / f"{jd_file.stem}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jd_data, f, indent=2, ensure_ascii=False)
            
            print(f"Successfully processed and saved: {output_file.name}")
            
        except Exception as e:
            print(f"Critical error processing {jd_file.name}: {str(e)}")
            continue

    print("Job description processing completed!")
    return