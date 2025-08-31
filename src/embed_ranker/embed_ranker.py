import json
from pathlib import Path
from ..utils import Candidates, JobMatchingResult, CandidateMatch, IndividualScore
from .embed_utils import parse_years, calculate_normalized_score, weights
from .similarity_calculator import encode_data, calculate_similarity, compute_fuzzy_match, compute_fuzzy_education_match
from ..config_loader import config


def rank_resumes(resumes_dir: str, jd_file: str, output_dir: str) -> None:
    """
    Rank resumes against a job description using embedding-based similarity for specified categories
    and fuzzy matching for others, including overall relevance.
    """
    resumes_path = Path(resumes_dir)
    jd_path = Path(jd_file)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if not resumes_path.exists():
        raise FileNotFoundError(f"Resumes directory does not exist: {resumes_dir}")
    if not jd_path.exists():
        raise FileNotFoundError(f"Job description file does not exist: {jd_file}")

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

    # Load existing results if any
    existing_candidates = []
    existing_file_names = set()
    output_file = output_path / f"{jd_path.stem}_ranked_resumes.json"
    if output_file.exists():
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                existing_result = json.load(f)
            existing_candidates = [CandidateMatch.parse_obj(c) for c in existing_result.get("candidates", {}).get("candidates", [])]
            existing_file_names = {c.file_name for c in existing_candidates}
            print(f"Found {len(existing_candidates)} already ranked candidates, skipping them.")
        except Exception as e:
            print(f"Error loading existing results, will overwrite. Reason: {str(e)}")

    resume_files_to_process = [rf for rf in resume_files if rf.stem not in existing_file_names]
    if not resume_files_to_process:
        print("All candidates already ranked, nothing new to process.")
        return

    print(f"Processing {len(resume_files_to_process)} new resumes...")
    
    # Pre-calculate JD embeddings once
    jd_job_title_emb = encode_data(jd_data.get("job_title", ""))
    jd_skills_emb = encode_data(" ".join(jd_data.get("required_skills", []) + jd_data.get("preferred_skills", [])))
    jd_education_emb = encode_data(" ".join([jd_data.get("required_education", "") or "", jd_data.get("preferred_education", "") or ""]))
    jd_responsibilities_emb = encode_data(" ".join(jd_data.get("responsibilities", [])))
    jd_soft_skills_emb = encode_data(" ".join(jd_data.get("soft_skills", [])))
    jd_domain_knowledge_emb = encode_data(" ".join(jd_data.get("required_domain_knowledge", []) + jd_data.get("preferred_domain_knowledge", [])))
    jd_preferred_qualifications_emb = encode_data(" ".join(jd_data.get("preferred_skills", []) + jd_data.get("preferred_domain_knowledge", [])))


    new_candidates = []
    for resume_file in resume_files_to_process:
        try:
            with open(resume_file, 'r', encoding='utf-8') as f:
                resume_data = json.load(f)

            # Encode resume sections
            resume_job_title_emb = encode_data(resume_data.get("job_title", ""))
            resume_skills_emb = encode_data(" ".join(resume_data.get("skills", [])))

            resume_education_text = " ".join([e.get("degree", "") + " " + e.get("field_of_study", "") for e in resume_data.get("education", [])])
            resume_education_emb = encode_data(resume_education_text)

            resume_experience_text = " ".join([e.get("description", "") + " " + " ".join(e.get("technologies_used", [])) for e in resume_data.get("experience", [])])
            resume_experience_emb = encode_data(resume_experience_text)

            resume_soft_skills_emb = encode_data(" ".join(resume_data.get("soft_skills", [])))
            resume_domain_knowledge_emb = encode_data(" ".join(resume_data.get("domain_knowledge", {}).get("industries", [])))
            resume_qualifications_emb = encode_data(" ".join(resume_data.get("skills", []) + resume_data.get("domain_knowledge", {}).get("industries", [])))

            # Calculate embedding similarity scores
            job_title_relevance = calculate_similarity(jd_job_title_emb, resume_job_title_emb)
            skills_embedding_score = calculate_similarity(jd_skills_emb, resume_skills_emb)
            education_embedding_score = calculate_similarity(jd_education_emb, resume_education_emb)
            experience_relevance = calculate_similarity(jd_responsibilities_emb, resume_experience_emb)
            soft_skills_relevance = calculate_similarity(jd_soft_skills_emb, resume_soft_skills_emb)
            domain_knowledge_match = calculate_similarity(jd_domain_knowledge_emb, resume_domain_knowledge_emb)
            preferred_qualifications_relevance = calculate_similarity(jd_preferred_qualifications_emb, resume_qualifications_emb)

            # Fuzzy matching for specified categories
            jd_required_skills = set(jd_data.get("required_skills", []))
            resume_skills_set = set(resume_data.get("skills", []))
            skills_fuzzy_score = compute_fuzzy_match(jd_required_skills, resume_skills_set)
            skills_match = config["scoring"]["embedding_score"] * skills_embedding_score + config["scoring"]["fuzzy_score"] * skills_fuzzy_score

            jd_required_education = jd_data.get("required_education", "")
            resume_education_list = [e.get("degree", "") + " " + e.get("field_of_study", "") for e in resume_data.get("education", [])]
            education_fuzzy_score = compute_fuzzy_education_match(jd_required_education, resume_education_list)
            education_match = config["scoring"]["embedding_score"] * education_embedding_score + config["scoring"]["fuzzy_score"] * education_fuzzy_score

            jd_experience_years = parse_years(jd_data.get("required_experience_duration", ""))
            resume_experience_years = parse_years(resume_data.get("experience_duration", ""))
            experience_years_score = min(100, (resume_experience_years / jd_experience_years * 100) if jd_experience_years else 50)

            jd_certifications = set(jd_data.get("required_certifications", []))
            resume_certifications = set(c.get("name", "") for c in resume_data.get("certifications", []))
            certifications_match = compute_fuzzy_match(jd_certifications, resume_certifications)

            jd_languages = set(jd_data.get("languages", []))
            resume_languages = set(resume_data.get("languages", []))
            languages_match = compute_fuzzy_match(jd_languages, resume_languages)

            jd_preferred_education = jd_data.get("preferred_education", "")
            preferred_education_score = compute_fuzzy_education_match(jd_preferred_education, resume_education_list)

            scores = IndividualScore(
                job_title_relevance=job_title_relevance,
                experience_years_match=experience_years_score,
                education_match=education_match,
                experience_relevance=experience_relevance,
                skills_match=skills_match,
                soft_skills_relevance=soft_skills_relevance,
                certifications_match=certifications_match,
                domain_knowledge_match=domain_knowledge_match,
                languages_match=languages_match,
                preferred_education_relevance=preferred_education_score,
                preferred_qualifications_relevance=preferred_qualifications_relevance
            )

            overall_score = calculate_normalized_score(scores, weights)
            candidate = CandidateMatch(
                name=resume_data.get("name", "Unknown"),
                file_name=resume_data.get("filename", resume_file.name),
                job_title=resume_data.get("job_title", ""),
                contact=resume_data.get("contact", {}),
                scores=scores,
                overall_score=round(overall_score, 2)
            )
            new_candidates.append(candidate)
            print(f"Processed candidate: {candidate.name} from {resume_file.name}")

        except Exception as e:
            print(f"Error processing resume {resume_file.name}: {str(e)}")
            continue

    candidate_dict = {c.file_name: c for c in existing_candidates}
    for candidate in new_candidates:
        candidate_dict[candidate.file_name] = candidate

    merged_candidates = list(candidate_dict.values())
    merged_candidates = sorted(merged_candidates, key=lambda x: x.overall_score, reverse=True)
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


def rank_job_descriptions_with_embeddings(resumes_dir: str, jds_dir: str, output_dir: str) -> None:
    """
    Rank resumes against all job descriptions in a directory, saving each result in a separate JSON file.
    """
    jds_path = Path(jds_dir)
    if not jds_path.exists():
        raise FileNotFoundError(f"Job descriptions directory does not exist: {jds_dir}")

    jd_files = list(jds_path.glob("*.json"))
    if not jd_files:
        print("No job description files found in the directory.")
        return

    print(f"Found {len(jd_files)} job description files to process.")
    
    for jd_file in jd_files:
        try:
            print(f"Processing job description: {jd_file.name}")
            rank_resumes(resumes_dir, str(jd_file), output_dir)
            print("----------------------------------------")
        except Exception as e:
            print(f"Error processing job description {jd_file.name}: {str(e)}")
            continue

    print("All job descriptions processed!")