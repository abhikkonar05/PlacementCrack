import re
import math
from typing import List, Dict, Any, Tuple
from pypdf import PdfReader
import io

# Stopwords list to clean text
STOPWORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've", "you'll", "you'd",
    'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers',
    'herself', 'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which',
    'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if',
    'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between',
    'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
    'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why',
    'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not',
    'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should',
    "should've", 'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn', "couldn't",
    'didn', "didn't", 'doesn', "doesn't", 'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't",
    'ma', 'mightn', "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"
}

# Role-specific core keywords for evaluation
ROLE_KEYWORDS = {
    "software development": [
        "python", "javascript", "react", "node", "java", "c++", "c#", "sql", "git", "docker", 
        "aws", "data structures", "algorithms", "rest api", "testing", "ci/cd", "mongodb", 
        "postgresql", "html", "css", "system design", "microservices", "kubernetes", "typescript"
    ],
    "data science": [
        "python", "sql", "pandas", "numpy", "scikit-learn", "machine learning", "data analysis", 
        "statistics", "data visualization", "tableau", "matplotlib", "seaborn", "regression", 
        "classification", "clustering", "git", "jupyter", "excel", "power bi", "big data", 
        "spark", "probability", "data mining"
    ],
    "ai/ml": [
        "python", "pytorch", "tensorflow", "keras", "machine learning", "deep learning", "nlp", 
        "computer vision", "transformers", "hugging face", "scikit-learn", "numpy", "linear algebra", 
        "calculus", "reinforcement learning", "neural networks", "llm", "git", "opencv", 
        "tensorboard", "cuda", "model deployment", "mlops", "bert"
    ]
}

def clean_text(text: str) -> List[str]:
    """Cleans text by converting to lowercase, removing punctuation, and separating into words."""
    text = text.lower()
    # Replace non-alphabetic chars with spaces
    text = re.sub(r'[^a-z\s+#]', ' ', text)
    # Split by spaces and remove empty strings + stopwords
    words = [word for word in text.split() if word and word not in STOPWORDS]
    return words

def calculate_cosine_similarity(words1: List[str], words2: List[str]) -> float:
    """Calculates Cosine Similarity between two lists of words."""
    # Count term frequencies
    vec1 = {}
    vec2 = {}
    for w in words1:
        vec1[w] = vec1.get(w, 0) + 1
    for w in words2:
        vec2[w] = vec2.get(w, 0) + 1
        
    all_words = set(vec1.keys()).union(set(vec2.keys()))
    
    dot_product = 0.0
    norm_a = 0.0
    norm_b = 0.0
    
    for w in all_words:
        val_a = vec1.get(w, 0)
        val_b = vec2.get(w, 0)
        dot_product += val_a * val_b
        norm_a += val_a ** 2
        norm_b += val_b ** 2
        
    if norm_a == 0 or norm_b == 0:
        return 0.0
        
    return dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extracts all text from PDF bytes."""
    try:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        full_text = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                full_text += text + "\n"
        return full_text
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""

def evaluate_resume(resume_text: str, role: str) -> Dict[str, Any]:
    """Evaluates the resume text against the target role requirements."""
    role_key = role.lower().strip()
    # Default to software development if not found
    if role_key not in ROLE_KEYWORDS:
        role_key = "software_development" if "software" in role_key else "software development"
        if role_key not in ROLE_KEYWORDS:
            role_key = "software development"
            
    target_keywords = ROLE_KEYWORDS[role_key]
    
    # Clean resume text and job profile description
    cleaned_resume = clean_text(resume_text)
    cleaned_job = target_keywords # We compare directly against target skills
    
    # Check for direct keyword matches (case insensitive matching)
    matched_keywords = []
    missing_keywords = []
    
    resume_lower = resume_text.lower()
    
    for kw in target_keywords:
        # Match using word boundary or simple substring for multi-word phrases
        pattern = r'\b' + re.escape(kw) + r'\b'
        if re.search(pattern, resume_lower):
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
            
    # Calculate Keyword Match Score (0 to 100)
    match_percentage = (len(matched_keywords) / len(target_keywords)) * 100 if target_keywords else 0.0
    
    # Structural checks (checking if sections are present)
    sections = {
        "education": r"\b(education|university|college|degree|btech|mtech|bsc|msc|bca|mca)\b",
        "experience": r"\b(experience|work|employment|internship|project|history)\b",
        "skills": r"\b(skills|technologies|tools|languages|expertise)\b",
        "projects": r"\b(projects|academic projects|personal projects|portfolio)\b",
    }
    
    structure_score = 0
    missing_sections = []
    for section, regex in sections.items():
        if re.search(regex, resume_lower):
            structure_score += 25
        else:
            missing_sections.append(section.capitalize())
            
    # Calculate overall ATS score: 60% keyword match + 30% structural compliance + 10% density/length check
    word_count = len(resume_text.split())
    length_score = 0
    if 250 <= word_count <= 800:
        length_score = 100
    elif 150 <= word_count < 250 or 800 < word_count <= 1200:
        length_score = 70
    else:
        length_score = 40
        
    overall_score = round((match_percentage * 0.6) + (structure_score * 0.3) + (length_score * 0.1), 1)
    
    # Generate tailored suggestions
    suggestions = []
    if missing_keywords:
        suggestions.append(f"Consider adding key tech skills: {', '.join(missing_keywords[:5])}.")
    if missing_sections:
        suggestions.append(f"Missing core resume sections: {', '.join(missing_sections)}. Try formatting them clearly.")
    if word_count < 250:
        suggestions.append("Your resume is very short. Expand on projects and work experience descriptions.")
    elif word_count > 800:
        suggestions.append("Your resume is quite long. Keep it concise, ideally fitting on a single page (under 800 words).")
    if not re.search(r'\b(github|linkedin)\b', resume_lower):
        suggestions.append("Add links to your professional profiles (GitHub, LinkedIn) to increase recruiter engagement.")
    if re.search(r'\b(i|me|my|we|our)\b', resume_lower):
        suggestions.append("Avoid first-person pronouns (I, my, we). Use action verbs and passive voice for descriptions.")
        
    if overall_score >= 80:
        suggestions.append("Excellent! Your resume is highly optimized for ATS scanners in this domain.")
    elif overall_score >= 50:
        suggestions.append("Good start, but adding missing domain keywords and structured segments will boost your score.")
    else:
        suggestions.append("Needs revision. Standardize sections and write detailed impact descriptions with relevant keywords.")
        
    return {
        "score": overall_score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions,
        "metrics": {
            "keyword_match": round(match_percentage, 1),
            "structure_compliance": structure_score,
            "formatting_length": length_score
        }
    }
