import os
from typing import Dict

import gradio as gr
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from src.ui_utils import process_files_pipeline,save_dataframe_to_csv

llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0,api_key=os.getenv("GOOGLE_API_KEY"))


def create_gradio_interface():
    theme = gr.themes.Soft()

    with gr.Blocks(title="TalentRanker", theme=theme, css="""
        .upload-box .file-input {
            min-height: 60px !important; /* smaller upload box */
        }
        .download-icon {
            cursor: pointer;
            margin-left: 10px;
            color: #2563eb;
            font-size: 16px;
        }
        .download-icon:hover {
            color: #1d4ed8;
        }
        .job-title-header {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        .enhance-checkbox {
            margin: 1rem 0;
        }
    """) as interface:

        # Header
        gr.HTML("""
            <div style="text-align: center; margin-bottom: 1.25rem;">
                <h1 style="font-size: 2.2rem; margin: 0;">TalentRanker</h1>
                <p style="margin: .25rem 0 0; color: gray;">AI-Powered Resume Ranking & Candidate Matching</p>
            </div>
        """)

        # Uploads 
        gr.HTML("<h2 style='margin: .25rem 0 0.75rem;'>Upload Files</h2>")
        with gr.Row():
            with gr.Column(scale=1):
                resume_upload = gr.File(
                    label="Upload Resume Files",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"],
                    elem_classes=["upload-box"]
                )
            with gr.Column(scale=1):
                jd_upload = gr.File(
                    label="Upload Job Description Files",
                    file_count="multiple",
                    file_types=[".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"],
                    elem_classes=["upload-box"]
                )
            with gr.Column(scale=1):
                process_btn = gr.Button("Process & Rank Candidates", variant="primary")
                clear_btn = gr.Button("Clear", variant="secondary")
                enhance_ai_checkbox = gr.Checkbox(
                    label="Enhance ranking with AI",
                    value=False,
                    info="Use AI for enhanced extraction and scoring.",
                    elem_classes=["enhance-checkbox"]
                )
                enhance_conversion_checkbox = gr.Checkbox(
                    label="Enhance conversion with AI",
                    value=False,
                    info="Use Docling for document conversion (slower but more accurate).",
                    elem_classes=["enhance-checkbox"]
                )

        status_output = gr.Textbox(label="Status", interactive=False, max_lines=3)

        # Persistent state across UI switches
        all_results_data = gr.State({})

        results_section = gr.Column(visible=False)

        def process_files(resumes, jds, enhance_with_ai,enhance_conversion):
            if not resumes or not jds:
                return "Please upload both resume and job description files.", {}, gr.update(visible=False)
            status, job_results = process_files_pipeline(resumes, jds, llm, enhance_with_ai,enhance_conversion)
            return status, job_results, gr.update(visible=True)

        def do_clear():
            return "", {}, gr.update(visible=False)

        def handle_csv_download(job_title: str, job_results: Dict[str, pd.DataFrame]) -> str:
            """Handle CSV download and return status message"""
            return save_dataframe_to_csv(job_title, job_results)

        with results_section:
            gr.HTML("<h2 style='margin-top: .5rem;'>Ranking Results</h2>")

            # CSV download status message
            csv_status = gr.Textbox(
                label="CSV Export Status", 
                interactive=False, 
                visible=False,
                max_lines=2
            )

            @gr.render(inputs=all_results_data)
            def render_results(job_results: Dict[str, pd.DataFrame]):
                if not job_results:
                    gr.HTML("<p style='color: gray;'>No results yet. Upload files, then click <b>Process & Rank Candidates</b>.</p>")
                    return

                # One dataframe per job
                for job_title, job_data in job_results.items():
                    df: pd.DataFrame = job_data

                    # Create header with download button
                    with gr.Row():
                        with gr.Column(scale=8):
                            gr.Markdown(f"### {job_title}")
                        with gr.Column(scale=1, min_width=80):
                            download_btn = gr.Button(
                                "📥 CSV", 
                                size="sm",
                                variant="secondary",
                                elem_id=f"download_{job_title.replace(' ', '_')}"
                            )
                    
                    # DataFrame display
                    gr.DataFrame(
                        value=df[["Rank","Candidate Name", "Current Job Title", "Phone", "Email", "LinkedIn", "Overall Score", "Resume File"]],
                        interactive=True,
                        wrap=True,
                        label=f"Results for {job_title}"
                    )
                    
                    # Connect download button to function
                    download_btn.click(
                        fn=lambda jt=job_title: handle_csv_download(jt, job_results),
                        outputs=csv_status
                    ).then(
                        fn=lambda: gr.update(visible=True),
                        outputs=csv_status
                    )

        process_btn.click(
            fn=process_files,
            inputs=[resume_upload, jd_upload, enhance_ai_checkbox,enhance_conversion_checkbox],
            outputs=[status_output, all_results_data, results_section],
        )

        clear_btn.click(
            fn=do_clear,
            outputs=[status_output, all_results_data, results_section],
        )

    return interface


def main():
    interface = create_gradio_interface()
    interface.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        debug=True
    )

if __name__ == "__main__":
    main()