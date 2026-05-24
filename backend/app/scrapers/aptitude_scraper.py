import asyncio
import httpx
import logging
import random
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from sqlalchemy import select
from app.database import SessionLocal
from app.models import AptitudeQuestion
from app.scrapers.utils import get_random_user_agent, random_anti_block_delay

logger = logging.getLogger("app.scrapers.aptitude_scraper")

# Rich curated fallback aptitude question bank to satisfy Quantitative, Logical, and Verbal preparation tracks
CURATED_APTITUDE_QUESTIONS = [
    # Quantitative Aptitude
    {
        "question": "A train running at the speed of 60 km/hr crosses a pole in 9 seconds. What is the length of the train?",
        "options": ["120 metres", "150 metres", "324 metres", "180 metres"],
        "answer": "150 metres",
        "explanation": "Speed = 60 km/hr = 60 * (5/18) m/sec = 50/3 m/sec.\nLength of the train = (Speed * Time) = (50/3 * 9) = 150 metres.",
        "category": "Quantitative",
        "difficulty": "Beginner",
    },
    {
        "question": "The average of 20 numbers is zero. Of them, at the most, how many may be greater than zero?",
        "options": ["0", "1", "10", "19"],
        "answer": "19",
        "explanation": "Average of 20 numbers = 0.\nTherefore, Sum of 20 numbers = (0 * 20) = 0.\nAt the most, 19 of these numbers may be positive (greater than 0) and their sum could be balanced out by a single strongly negative 20th number to result in a sum of 0.",
        "category": "Quantitative",
        "difficulty": "Intermediate",
    },
    {
        "question": "A, B and C can do a piece of work in 20, 30 and 60 days respectively. In how many days can A do the work if he is assisted by B and C on every third day?",
        "options": ["12 days", "15 days", "16 days", "18 days"],
        "answer": "15 days",
        "explanation": "A's 2 days work = 2 * (1/20) = 1/10.\n(A+B+C)'s 1 day work on the 3rd day = (1/20 + 1/30 + 1/60) = 6/60 = 1/10.\nWork done in 3 days = (1/10 + 1/10) = 1/5.\nTo complete the whole work (5/5), time taken = 3 * 5 = 15 days.",
        "category": "Quantitative",
        "difficulty": "Advanced",
    },
    # Logical Reasoning
    {
        "question": "SCD, TEF, UGH, ____, WKL. What letter block should fill the blank?",
        "options": ["CMN", "UJI", "VIJ", "IJT"],
        "answer": "VIJ",
        "explanation": "The first letters follow alphabetical order: S, T, U, V, W.\nThe second letters follow order: C, E, G, I, K (skipping one letter each time).\nThe third letters follow order: D, F, H, J, L (skipping one letter each time).\nCombining these gives: V, I, J.",
        "category": "Logical",
        "difficulty": "Beginner",
    },
    {
        "question": "Point A is 5m West of B. Point C is 10m South of B. Point D is 5m East of C. In which direction is A with respect to D?",
        "options": ["North-West", "North-East", "South-West", "North"],
        "answer": "North-West",
        "explanation": "Point A is West of B. Point C is directly South of B. Point D is East of C.\nThis forms a rectangular system. D is 5m East of C, which means it lies directly South of B. \nTherefore, Point A (West of B) is in the North-West direction relative to D.",
        "category": "Logical",
        "difficulty": "Intermediate",
    },
    # Verbal Ability
    {
        "question": "Choose the word which is most similar in meaning to: 'OBSTINATE'",
        "options": ["Flexible", "Stubborn", "Miserable", "Cooperative"],
        "answer": "Stubborn",
        "explanation": "'Obstinate' means refusing to change one's behavior or ideas; stubborn. Hence, 'Stubborn' is the correct synonym.",
        "category": "Verbal",
        "difficulty": "Beginner",
    },
    {
        "question": "Complete the sentence: 'The director was so impressed by the candidate's ______ that he hired him immediately.'",
        "options": ["apathy", "eloquence", "lethargy", "indecision"],
        "answer": "eloquence",
        "explanation": "'Eloquence' means fluent or persuasive speaking or writing, which is a positive attribute that would impress a director and lead to an immediate hire. Other options represent negative attributes.",
        "category": "Verbal",
        "difficulty": "Intermediate",
    }
]

async def scrape_aptitude_questions() -> int:
    """Attempts to dynamically scrape aptitude questions. Falls back cleanly to our rich static question bank."""
    scraped_count = 0
    scraped_questions = []
    
    # Target URL: Public aptitude repository metadata
    target_url = "https://raw.githubusercontent.com/suyash/aptitude/master/data/logical_reasoning.json"
    
    try:
        logger.info("Initiating dynamic aptitude question scrape...")
        headers = {"User-Agent": get_random_user_agent()}
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(target_url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for item in data.get("questions", [])[:20]: # Limit size
                    # Validate required fields
                    question_text = item.get("question")
                    options = item.get("options")
                    answer = item.get("answer")
                    
                    if question_text and options and answer:
                        scraped_questions.append({
                            "question": question_text,
                            "options": options,
                            "answer": answer,
                            "explanation": item.get("explanation", "Please refer to standard reasoning rules to verify."),
                            "category": "Logical",
                            "difficulty": random.choice(["Beginner", "Intermediate", "Advanced"]),
                        })
        
        await random_anti_block_delay(0.5, 1.5)
        
    except Exception as e:
        logger.error(f"Live aptitude scrape skipped: {e}. Decoupling to fail-safe database mode.")
        
    # Fail-safe static merge
    if not scraped_questions:
        logger.info("Using curated aptitude fallback dataset.")
        scraped_questions = CURATED_APTITUDE_QUESTIONS
        
    # Save/Upsert to PostgreSQL (select-then-update/insert since question column has no unique constraint)
    async with SessionLocal() as session:
        try:
            for q in scraped_questions:
                try:
                    # Check if question already exists
                    existing_stmt = select(AptitudeQuestion).where(
                        AptitudeQuestion.question == q["question"]
                    )
                    existing_result = await session.execute(existing_stmt)
                    existing_row = existing_result.scalar_one_or_none()
                    
                    if existing_row:
                        # Update existing record
                        existing_row.options = q["options"]
                        existing_row.answer = q["answer"]
                        existing_row.explanation = q.get("explanation")
                        existing_row.category = q["category"]
                        existing_row.difficulty = q["difficulty"]
                        session.add(existing_row)
                    else:
                        # Insert new record
                        new_question = AptitudeQuestion(
                            question=q["question"],
                            options=q["options"],
                            answer=q["answer"],
                            explanation=q.get("explanation"),
                            category=q["category"],
                            difficulty=q["difficulty"],
                        )
                        session.add(new_question)
                    
                    scraped_count += 1
                except Exception as db_err:
                    logger.error(f"Failed to record aptitude question: {db_err}")
            
            await session.commit()
        except Exception as commit_err:
            await session.rollback()
            logger.error(f"Failed to commit aptitude questions batch: {commit_err}")
            
    logger.info(f"Recorded {scraped_count} unique aptitude questions in PostgreSQL.")
    return scraped_count
