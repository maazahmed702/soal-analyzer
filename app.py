import streamlit as st
import google.generativeai as genai
import os
import PyPDF2 as pdf
import json
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_gemini_response(input_prompt):
    """Fetch response from Gemini AI and ensure it returns JSON."""
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(input_prompt)
    return response.text.strip()

def extract_json(text):
    """Extract JSON from AI response using regex."""
    json_match = re.search(r'\{.*\}', text, re.DOTALL)
    return json.loads(json_match.group()) if json_match else None

def input_pdf_text(uploaded_file):
    """Extract text from an uploaded PDF."""
    try:
        reader = pdf.PdfReader(uploaded_file)
        text = "\n".join(page.extract_text() for page in reader.pages if page.extract_text())
        return text.strip() if text else None
    except Exception:
        return None

def generate_mcqs(job_description):
    """Generate technical MCQs based on job description."""
    mcq_prompt = f"""
    Generate 5 multiple-choice technical questions based on the job description below.
    Format your response as a JSON object, without any extra text.

    {{
        "questions": [
            {{
                "question": "What does XYZ mean?",
                "options": ["Option1", "Option2", "Option3", "Option4"],
                "correct_answer": "Option2"
            }}
        ]
    }}

    Job Description: {job_description}
    """
    response = get_gemini_response(mcq_prompt)
    return extract_json(response).get("questions", []) if extract_json(response) else []

st.set_page_config(page_title="SOAL Resume Optimizer", layout="wide")

# Custom CSS for Styling
st.markdown("""
    <style>
        .main-header { text-align: center; color: #333; font-size: 36px; font-weight: bold; }
        .sub-header { text-align: center; color: #666; font-size: 20px; margin-bottom: 20px; }
        .stTextArea, .stFileUploader, .stButton { width: 80%; margin: auto; }
        .stButton button { background-color: #ff7f50; color: white; font-size: 18px; border-radius: 8px; }
        .stButton button:hover { background-color: #ff4500; }

        /* Fix for white background issue */
        .result-container { 
            padding: 20px; 
            background: #2d2d2d; /* Dark background */
            color: white;  /* White text */
            border-radius: 10px;
            margin-top: 20px;
        }

        .match-percentage { font-size: 24px; font-weight: bold; color: #ff7f50; }
    </style>
""", unsafe_allow_html=True)

# Sidebar with Logo Only (No Candidate Assessment Option)
st.sidebar.image("WhatsApp Image 2025-03-13 at 03.22.21_b9d384a5.jpg", width=200)

# Main Page Title
st.markdown("<h1 class='main-header'>SOAL'S RESUME OPTIMIZER</h1>", unsafe_allow_html=True)
st.markdown("<h2 class='sub-header'>Analyze The Resume</h2>", unsafe_allow_html=True)

# Job Description Input and Resume Upload
jd = st.text_area("Paste the Job Description")
uploaded_file = st.file_uploader("Upload Your Resume", type="pdf")

if st.button("Submit"):
    if uploaded_file is not None and jd.strip():
        text = input_pdf_text(uploaded_file)
        if not text:
            st.error("Error: Unable to extract text from PDF.")
        else:
            formatted_prompt = f"""
            Compare the resume below with the provided job description.
            Format your response as a JSON object, without any extra text.

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
            json_data = extract_json(response)

            if json_data:
                match_percentage = int(json_data.get('JD Match', '0%').replace('%', ''))

                st.markdown(f"""
                <div class='result-container'>
                    <h3>Analysis Results</h3>
                    <p><b>Match Percentage:</b> <span class='match-percentage'>{match_percentage}%</span></p>
                    <p><b>Matching Keywords:</b> {', '.join(json_data.get('MatchingKeywords', []))}</p>
                    <p><b>Missing Keywords:</b> {', '.join(json_data.get('MissingKeywords', []))}</p>
                    <p><b>Profile Summary:</b> {json_data.get('Profile Summary', 'N/A')}</p>
                    <p><b>Resume Improvement Tips:</b> {json_data.get('ImprovementSuggestion', 'N/A')}</p>
                </div>
                """, unsafe_allow_html=True)

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

                        if st.button("Submit Answers"):
                            correct_count = sum(1 for i, mcq in enumerate(mcqs) if user_answers[i] == mcq["correct_answer"])
                            st.write(f"✅ You got {correct_count} out of {len(mcqs)} correct!")
                            st.write("Keep improving your skills for better results.")

            else:
                st.error("Error: AI response was not valid JSON. Try again.")
                st.text(f"Raw AI Response:\n{response}")

    else:
        st.error("Please upload a resume and provide a job description.")
