import json
from pathlib import Path
from typing import Dict
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from .utils import ResumeData,default_resume
from .prompts import RESUME_EXTRACTION_PROMPT
from datetime import datetime
current_date = datetime.now().strftime("%B %Y")




def process_resume_file(resume_file: Path, llm: BaseLanguageModel) -> Dict:
    """
    Process a resume markdown file and extract structured data using Gemini API.
    
    Args:
        resume_file (Path): Path to the resume markdown file
        llm (BaseLanguageModel): Language model instance for processing

    Returns:
        Dict: Extracted resume data as dictionary
    """
    try:
        # Read the file content
        with open(resume_file, 'r', encoding='utf-8') as f:
            resume_text = f.read()
        
        print(f"Processing resume from: {resume_file.name}")
        
        prompt = PromptTemplate(template=RESUME_EXTRACTION_PROMPT,input_variables=["current_date","resume_text"])

        # Initialize the LLM
        structured_llm = llm.with_structured_output(ResumeData)
        chain = prompt | structured_llm

        resume_data = chain.invoke({"current_date": current_date,"resume_text": resume_text})

        result = resume_data.dict()
        result['filename'] = resume_file.name
        
        return result
        
    except Exception as e:
        print(f"Error processing resume from {resume_file.name}: {str(e)}")
        # Return a default ResumeData object
        result=default_resume.dict()
        result['filename'] = resume_file.name
        return result


def process_resumes_directory( resumes_dir: str, output_dir: str, llm: BaseLanguageModel) -> None:
    """
    Process all resume markdown files in a directory and save each as a separate JSON file.
    
    Args:
        resumes_dir (str): Directory containing resume markdown files
        output_dir (str): Directory to save processed resumes JSON files
        llm (BaseLanguageModel): Language model instance for processing

    Returns:
        None
        
    Raises:
        FileNotFoundError: If the resumes directory doesn't exist
    """
    resumes_path = Path(resumes_dir)
    if not resumes_path.exists():
        raise FileNotFoundError(f"Directory {resumes_dir} does not exist")
    
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Get all markdown files
    md_files = list(resumes_path.glob("*.md"))
    total_files = len(md_files)
    
    if total_files == 0:
        print("No markdown files found in the directory")
        return
    
    print(f"Found {total_files} resume files to process")
    print(f"Output will be saved to: {output_dir}")
    
    processed=0
    skipped=0
    for md_file in md_files:
        output_file = output_path / f"{md_file.stem}.json"
        if output_file.exists():
            print(f"Skipping already extracted file: {md_file.name}")
            skipped+=1
            continue
        try:
            # Process the resume file
            resume_data = process_resume_file(md_file,llm)
            
            # Save each resume as a separate JSON file
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(resume_data, f, indent=2, ensure_ascii=False)            
            processed+=1
        except Exception as e:
            print(f"Critical error processing {md_file.name}: {str(e)}")
            continue

    print(f"Processing completed! {processed} files extracted successfully, {skipped} skipped.")
    return


