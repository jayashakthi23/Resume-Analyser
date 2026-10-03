import os
import re
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from pypdf import PdfReader
from docx import Document
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "supersecretkey"
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(file_path):
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def extract_text_from_docx(file_path):
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    except Exception as e:
        print(f"Error reading DOCX: {e}")
        return ""

def load_skills():
    with open('skills.json', 'r') as f:
        return json.load(f)

def extract_skills(text, skills_db):
    found_skills = set()
    text = text.lower()
    for category, skills in skills_db.items():
        for skill in skills:
            pattern = r'\b' + skill['regex'] + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                found_skills.add(skill['name'])
    return list(found_skills)

def detect_sections(text):
    sections = {
        "Education": ["education", "academic", "qualification"],
        "Experience": ["experience", "employment", "work history", "work experience"],
        "Projects": ["projects", "personal projects", "technical projects"],
        "Skills": ["skills", "technical skills", "expertise", "competencies"],
        "Certifications": ["certifications", "licenses", "courses"],
        "Achievements": ["achievements", "awards", "honors"]
    }
    found_sections = []
    text_lower = text.lower()
    for section, keywords in sections.items():
        for keyword in keywords:
            if re.search(r'\b' + keyword + r'\b', text_lower):
                found_sections.append(section)
                break
    return found_sections

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'resume' not in request.files:
        flash("No file part")
        return redirect(request.url)
    
    file = request.files['resume']
    jd_text = request.form.get('job_description', '')

    if file.filename == '':
        flash("No selected file")
        return redirect(request.url)

    if not jd_text.strip():
        flash("Job description is empty")
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Extract text
        if filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(file_path)
        else:
            resume_text = extract_text_from_docx(file_path)

        # Cleanup file immediately
        if os.path.exists(file_path):
            os.remove(file_path)

        if not resume_text.strip():
            flash("Could not extract text from the file. It might be empty or corrupt.")
            return redirect(url_for('index'))

        # Analysis
        skills_db = load_skills()
        resume_skills = extract_skills(resume_text, skills_db)
        jd_skills = extract_skills(jd_text, skills_db)

        if not jd_skills:
            flash("No skills detected in the Job Description. Please provide a more detailed JD.")
            return redirect(url_for('index'))

        matched_skills = [s for s in jd_skills if s in resume_skills]
        missing_skills = [s for s in jd_skills if s not in resume_skills]
        
        match_percentage = round((len(matched_skills) / len(jd_skills)) * 100) if jd_skills else 0
        
        detected_sections = detect_sections(resume_text)

        # Recommendations (simple rule: suggest learning missing skills)
        recommendations = missing_skills[:5]

        return render_template('result.html', 
                               match_percentage=match_percentage,
                               matched_skills=matched_skills,
                               missing_skills=missing_skills,
                               resume_skills=resume_skills,
                               jd_skills=jd_skills,
                               detected_sections=detected_sections,
                               recommendations=recommendations)

    flash("Invalid file type. Only PDF and DOCX are allowed.")
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
