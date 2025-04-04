import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini AI
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Function to get response from Gemini AI
def get_gemini_response(input_prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input_prompt)
    return response.text

# Function to extract text from PDF
def input_pdf_text(uploaded_file):
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            extracted_text = page.extract_text()
            if extracted_text:
                text += extracted_text + "\n"
        return text.strip() if text else None
    except Exception:
        return None

# Function to generate technical MCQs
def generate_mcqs(job_description):
    mcq_prompt = f"""
    Generate 5 multiple-choice technical questions based on the following job description. 
    Format the response strictly as JSON:

    {{
        "questions": [
            {{
                "question": "Question text here",
                "options": ["Option1", "Option2", "Option3", "Option4"],
                "correct_answer": "Correct Option"
            }}
        ]
    }}

    Job Description: {job_description}
    """

    response = get_gemini_response(mcq_prompt)

    try:
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        return json.loads(json_match.group())["questions"] if json_match else []
    except (json.JSONDecodeError, ValueError):
        return []

# Streamlit App UI
st.set_page_config(page_title="SOAL Resume Optimizer", layout="wide")

# Sidebar Navigation
st.sidebar.image("WhatsApp Image 2025-03-13 at 03.22.21_b9d384a5.jpg", width=200)
st.sidebar.title("Navigation")
page = st.sidebar.radio("Select Option:", ["Resume Matching", "Candidate Assessment"])

if page == "Resume Matching":
    st.title("SOAL'S RESUME OPTIMIZER")
    st.text("Analyze The Resume")

    # User inputs
    jd = st.text_area("Paste the Job Description")
    uploaded_file = st.file_uploader("Upload Your Resume", type="pdf")

    # Submit button
    submit = st.button("Submit")

    if submit:
        if uploaded_file is not None and jd.strip():
            text = input_pdf_text(uploaded_file)

            if not text:
                st.error("Error: Unable to extract text from PDF.")
            else:
                formatted_prompt = f"""
                Compare the following resume with the provided job description and return JSON:

                {{
                    "JD Match": "XX%", 
                    "MatchingKeywords": ["keyword1", "keyword2"],
                    "MissingKeywords": ["keyword1", "keyword2"],
                    "Profile Summary": "Summary of candidate",
                    "ImprovementSuggestion": "Ways to enhance resume"
                }}

                ### Resume: {text}
                ### Job Description: {jd}
                """

                response = get_gemini_response(formatted_prompt)

                try:
                    json_match = re.search(r'\{.*\}', response, re.DOTALL)
                    parsed_response = json.loads(json_match.group()) if json_match else {}

                    # Display results
                    st.subheader("Analysis Results")
                    match_percentage = parsed_response.get('JD Match', '0%').replace('%', '')
                    match_percentage = int(match_percentage)

                    st.write(f"Match Percentage: {match_percentage}%")
                    st.write(f"Matching Keywords: {', '.join(parsed_response.get('MatchingKeywords', []))}")
                    st.write(f"Missing Keywords: {', '.join(parsed_response.get('MissingKeywords', []))}")
                    st.write(f"Profile Summary: {parsed_response.get('Profile Summary', 'N/A')}")
                    st.write(f"Resume Improvement Tips: {parsed_response.get('ImprovementSuggestion', 'N/A')}")

                    # If match is >= 70%, allow MCQ attempt
                    if match_percentage >= 70:
                        st.success("Your resume matches well with the job! You can now attempt a technical quiz.")
                        
                        mcqs = generate_mcqs(jd)
                        if not mcqs:
                            st.error("Failed to generate MCQs. Please try again.")
                        else:
                            st.subheader("Technical MCQs")

                            user_answers = {}
                            for i, mcq in enumerate(mcqs):
                                st.write(f"{i+1}. {mcq['question']}")
                                user_answers[i] = st.radio(
                                    f"Choose an option for Question {i+1}:",
                                    mcq["options"],
                                    key=f"mcq_{i}"
                                )

                            # Submit button for MCQ
                            if st.button("Submit Answers"):
                                correct_count = sum(1 for i, mcq in enumerate(mcqs) if user_answers[i] == mcq["correct_answer"])
                                st.write(f"✅ You got {correct_count} out of {len(mcqs)} correct!")
                                st.write("Keep improving your skills for better results.")

                except json.JSONDecodeError:
                    st.error("Error: The AI response is not in a valid JSON format. Please try again.")
                    st.text(f"Raw AI Response:\n{response}")  # Debug info

        else:
            st.error("Please upload a resume and provide a job description.")