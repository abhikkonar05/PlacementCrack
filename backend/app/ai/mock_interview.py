import json
import logging
from typing import List, Dict, Any, Tuple
from app.config import settings
from app.ai.huggingface_client import (
    evaluate_answer_with_huggingface,
    generate_questions_with_huggingface,
)

logger = logging.getLogger("app.ai.mock_interview")

# Fallback questions database
QUESTIONS = {
    "software development": [
        "Explain the difference between a process and a thread. When would you use multi-threading over multi-processing?",
        "What are the SOLID principles of Object-Oriented Design? Can you explain the Single Responsibility Principle and its benefits?",
        "Explain how collision resolution works in a Hash Map. What is the average and worst-case time complexity of lookup?",
        "How would you design a scalable URL shortener service (like bit.ly)? What databases and caching mechanisms would you use?"
    ],
    "data science": [
        "Explain the bias-variance tradeoff in machine learning. How does it relate to overfitting and underfitting?",
        "What is regularization in regression models? What is the main difference between L1 (Lasso) and L2 (Ridge) regularization?",
        "How would you handle a highly imbalanced dataset where the positive class is only 1% of the data?",
        "Explain the difference between bagging and boosting ensemble techniques. Give an example algorithm for each."
    ],
    "ai/ml": [
        "What is the vanishing gradient problem in deep neural networks? How do modern architectures (like ResNets) or activation functions mitigate it?",
        "Explain the self-attention mechanism in Transformer models. Why is it superior to recurrent architectures (LSTMs)?",
        "What is the difference between transfer learning and fine-tuning? When would you use one over the other?",
        "Explain MLOps. How do you monitor machine learning models in production for data drift and concept drift?"
    ]
}

# Setup Grok safely
has_grok = False
grok_client = None
if settings.GROK_API_KEY:
    try:
        # pyrefly: ignore [missing-import]
        from openai import AsyncOpenAI
        grok_client = AsyncOpenAI(
            api_key=settings.GROK_API_KEY,
            base_url="https://api.x.ai/v1"
        )
        has_grok = True
        logger.info("Grok API initialized successfully for mock interviews.")
    except Exception as e:
        logger.error(f"Failed to configure Grok API: {e}")

def get_fallback_interview_questions(role: str) -> List[str]:
    """Retrieves standard interview questions based on the target role."""
    role_key = role.lower().strip()
    if role_key not in QUESTIONS:
        if "software" in role_key:
            role_key = "software development"
        elif "data" in role_key:
            role_key = "data science"
        else:
            role_key = "ai/ml"
    return QUESTIONS[role_key]

async def get_interview_questions(role: str) -> List[str]:
    """Generate role-specific interview questions from Hugging Face, with local fallback."""
    hf_questions = await generate_questions_with_huggingface(role)
    if hf_questions:
        return hf_questions
    return get_fallback_interview_questions(role)

async def generate_feedback_grok(role: str, question: str, answer: str) -> Tuple[float, str]:
    """Generates grading score and text feedback using Grok API."""
    hf_result = await evaluate_answer_with_huggingface(role, question, answer)
    if hf_result:
        feedback = hf_result["feedback"]
        if hf_result["improvement_tips"]:
            feedback += "\n\nActionable Improvement: " + hf_result["improvement_tips"]
        return hf_result["score"], feedback

    if not has_grok or not grok_client:
        return evaluate_locally(question, answer)
        
    try:
        prompt = f"""
        You are an expert technical interviewer hiring for a {role} position.
        Evaluate the candidate's response to the following question.
        
        Question: {question}
        Candidate's Answer: {answer}
        
        Provide your response strictly in the following JSON format:
        {{
            "score": <score out of 100, float>,
            "feedback": "<detailed constructive feedback on the response, highlighting strengths and weaknesses>",
            "improvement_tips": "<specific tips on what keywords or concepts are missing or can be explained better>"
        }}
        """
        
        # Call model
        response = await grok_client.chat.completions.create(
            model="grok-beta",
            messages=[
                {"role": "system", "content": "You are a helpful AI JSON output generator."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        text = response.choices[0].message.content.strip()
        
        data = json.loads(text)
        score = float(data.get("score", 70.0))
        feedback = data.get("feedback", "") + "\n\n**Actionable Improvement:** " + data.get("improvement_tips", "")
        return score, feedback
    except Exception as e:
        logger.error(f"Error calling Grok API: {e}")
        return evaluate_locally(question, answer)

def evaluate_locally(question: str, answer: str) -> Tuple[float, str]:
    """Local, rule-based feedback system when Gemini API is unavailable."""
    word_count = len(answer.split())
    if word_count < 10:
        return 20.0, "Your response is too brief. Try to explain the concepts in detail, mentioning key terms and implementation contexts."
        
    score = 50.0
    feedback_points = []
    
    # 1. Structure evaluation
    if any(phrase in answer.lower() for phrase in ["for example", "e.g.", "such as", "instance"]):
        score += 15
        feedback_points.append("Good job using examples to illustrate your point.")
    else:
        feedback_points.append("Consider providing real-world examples to demonstrate practical understanding.")
        
    if any(phrase in answer.lower() for phrase in ["because", "therefore", "leads to", "since", "due to"]):
        score += 10
        feedback_points.append("You structured your logic well using causal connectives.")
        
    # 2. Length check
    if 50 <= word_count <= 150:
        score += 15
        feedback_points.append("Response length is perfect for a standard interview reply.")
    elif word_count > 150:
        score += 10
        feedback_points.append("Response is thorough, though ensure you remain concise to keep the interviewer engaged.")
    else:
        score += 5
        feedback_points.append("Try to expand your explanation slightly (aim for 50-100 words).")
        
    # 3. Domain keyword checking (general keywords)
    key_phrases = ["scalability", "complexity", "tradeoff", "performance", "optimization", "efficiency", "architecture"]
    matched = [kp for kp in key_phrases if kp in answer.lower()]
    if matched:
        score += len(matched) * 3
        feedback_points.append(f"Great use of domain terminology like: {', '.join(matched)}.")
        
    # Cap score at 95 (since 100 is reserved for exceptional responses)
    final_score = min(score, 95.0)
    
    feedback = " ".join(feedback_points)
    return final_score, feedback

async def evaluate_full_interview(role: str, questions: List[str], answers: List[str]) -> Tuple[float, List[Dict[str, Any]]]:
    """Evaluates all questions and answers in a mock interview, generating a total scorecard."""
    detailed_evaluations = []
    total_score = 0.0
    
    for i, (q, a) in enumerate(zip(questions, answers)):
        score, feedback = await generate_feedback_grok(role, q, a)
        detailed_evaluations.append({
            "question_number": i + 1,
            "question": q,
            "answer": a,
            "score": score,
            "feedback": feedback
        })
        total_score += score
        
    average_score = round(total_score / len(questions), 1) if questions else 0.0
    return average_score, detailed_evaluations