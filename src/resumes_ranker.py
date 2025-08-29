import json
from pathlib import Path
from langchain_core.prompts import PromptTemplate
from langchain_core.language_models import BaseLanguageModel
from src.utils import  Candidates, JobMatchingResult
from src.prompts import RESUME_JOB_SCORING_PROMPT


weights = {
        "job_title_relevance": 0.03,
        "experience_years_match": 0.20,
        "education_match": 0.20,
        "experience_relevance": 0.08,
        "skills_match": 0.20,
        "soft_skills_relevance": 0.04,
        "certifications_match": 0.05,
        "domain_knowledge_match": 0.04,
        "languages_match": 0.10,
        "preferred_education_relevance": 0.03,
        "preferred_qualifications_relevance": 0.03
    }


def rank_resumes(resumes_dir: str, jd_file: str, llm: BaseLanguageModel, output_dir: str, batch_size: int = 10) -> None:
    """
    Rank resumes against a single job description by sending batches of resumes in a single LLM request,
    expecting a list of CandidateMatch objects, and save results as a JSON file. Uses the 'filename' field
    from resume data instead of tracking file names separately.

    Args:
        resumes_dir (str): Directory containing resume JSON files.
        jd_file (str): Path to the job description JSON file.
        llm (BaseLanguageModel): Language model instance for processing.
        output_dir (str): Directory to save the output JSON file.
        batch_size (int): Number of resumes to process in each batch (default: 10).

    Returns:
        None
    """

    resumes_path = Path(resumes_dir)
    jd_path = Path(jd_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Validate inputs
    if not resumes_path.exists():
        raise FileNotFoundError(f"Resumes directory does not exist: {resumes_dir}")
    if not jd_path.exists():
        raise FileNotFoundError(f"Job description file does not exist: {jd_file}")

    # Load job description
    try:
        with open(jd_path, 'r', encoding='utf-8') as f:
            jd_data = json.load(f)
    except Exception as e:
        print(f"Error loading job description {jd_path.name}: {str(e)}")
        return

    # Get all resume JSON files
    resume_files = list(resumes_path.glob("*.json"))
    if not resume_files:
        print("No resume files found in the directory.")
        return

    print(f"Found {len(resume_files)} resume files to process for {jd_path.name}")

    # Output file for this JD
    output_file = output_path / f"{jd_path.stem}_ranked_resumes.json"

    # Load existing results if any
    existing_candidates = []
    existing_file_names = set()
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_result = json.load(f)
            existing_candidates = existing_result.get("candidates", {}).get("candidates", [])
            existing_file_names = {Path(c.get("file_name")).stem for c in existing_candidates}
            print(f"Found {len(existing_candidates)} already ranked candidates, skipping them.")
        except Exception as e:
            print(f"Error loading existing results, will overwrite. Reason: {str(e)}")

    # Filter resumes: only process new ones
    resume_files_to_process = [rf for rf in resume_files if rf.stem not in existing_file_names]
    if not resume_files_to_process:
        print("All candidates already ranked, nothing new to process.")
        return

    print(f"Processing {len(resume_files_to_process)} new resumes...")

    prompt = PromptTemplate(template=RESUME_JOB_SCORING_PROMPT,input_variables=["job_description", "resume_data", "weights"])
    structured_llm = llm.with_structured_output(Candidates)
    chain = prompt | structured_llm

    new_candidates = []
    total_new = len(resume_files_to_process)
    # Process in batches
    for i in range(0, total_new, batch_size):
        batch = resume_files_to_process[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        print(f"Processing batch {batch_num} of {total_new // batch_size + 1}")

        batch_resume_data = []
        for resume_file in batch:
            try:
                with open(resume_file, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                batch_resume_data.append(resume_data)
            except Exception as e:
                print(f"Error loading resume {resume_file.name}: {str(e)}")
                continue

        if not batch_resume_data:
            continue

        try:
            batch_candidates_response = chain.invoke({
                "job_description": json.dumps(jd_data),
                "resume_data": json.dumps(batch_resume_data),
                "weights": json.dumps(weights)
            })

            if not isinstance(batch_candidates_response, Candidates):
                print("LLM did not return a valid Candidates object")
                continue

            for candidate in batch_candidates_response.candidates:
                try:
                    new_candidates.append(candidate.dict())
                    print(f"Processed candidate: {candidate.name} from {candidate.file_name}")
                except Exception as e:
                    print(f"Error processing candidate: {str(e)}")
                    continue

        except Exception as e:
            print(f"Error processing batch {i // batch_size + 1}: {str(e)}")
            continue

    # Merge existing + new, ensuring no duplicates
    candidate_dict = {c.get("file_name"): c for c in existing_candidates}  # Existing candidates by file_name
    for candidate in new_candidates:
        candidate_dict[candidate.get("file_name")] = candidate  # Overwrite or add new candidates

    merged_candidates = list(candidate_dict.values())  # Convert back to list
    merged_candidates = sorted(merged_candidates, key=lambda x: x.get("overall_score", 0), reverse=True)

    # Save results
    result = JobMatchingResult(
        job_title=jd_data.get("job_title", "Unknown"),
        job_file_name=jd_path.name,
        candidates=Candidates(candidates=merged_candidates)
    ).dict()

    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Updated results saved to: {output_file}")
    except Exception as e:
        print(f"Error saving results: {str(e)}")

    print(f"Ranking completed for {jd_path.name}!")


def rank_job_descriptions(resumes_dir: str, jds_dir: str, llm: BaseLanguageModel, output_dir: str,batch_size:int=10) -> None:
    """
    Rank resumes against all job descriptions in a directory, saving each result in a separate JSON file.

    Args:
        resumes_dir (str): Directory containing resume JSON files.
        jds_dir (str): Directory containing job description JSON files.
        llm (BaseLanguageModel): Language model instance for processing.
        output_dir (str): Directory to save the output JSON files.
        batch_size (int): Number of resumes to process in each batch (default: 5).
    Returns:
        None
    """
    jds_path = Path(jds_dir)
    if not jds_path.exists():
        raise FileNotFoundError(f"Job descriptions directory does not exist: {jds_dir}")

    # Get all job description JSON files
    jd_files = list(jds_path.glob("*.json"))
    if not jd_files:
        print("No job description files found in the directory.")
        return

    print(f"Found {len(jd_files)} job description files to process.")

    for jd_file in jd_files:
        try:
            print(f"Processing job description: {jd_file.name}")
            rank_resumes(resumes_dir, str(jd_file), llm, output_dir, batch_size=batch_size)
            print("----------------------------------------")
        except Exception as e:
            print(f"Error processing job description {jd_file.name}: {str(e)}")
            continue

    print("All job descriptions processed!")