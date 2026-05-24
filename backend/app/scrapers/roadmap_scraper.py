import asyncio
import httpx
import logging
from datetime import datetime, timezone
from sqlalchemy.dialects.postgresql import insert as pg_insert
from app.database import SessionLocal
from app.models import Roadmap
from app.scrapers.utils import get_random_user_agent, random_anti_block_delay

logger = logging.getLogger("app.scrapers.roadmap_scraper")

# Extremely detailed, premium pre-curated career roadmaps for PlacementCrack preparation tracks
CURATED_ROADMAPS = [
    {
        "role": "Frontend Developer",
        "description": "Learn to design, build, and maintain highly interactive, user-facing web applications using modern styling, layouts, and JavaScript framework ecosystems.",
        "steps": [
            {"phase": "Phase 1: Internet & Web Fundamentals", "topics": ["How the Internet works", "HTTP/HTTPS protocols", "Domain Names and Hosting", "DNS and Web Servers"]},
            {"phase": "Phase 2: HTML & CSS Core", "topics": ["Semantic HTML5", "CSS3 Basics (Selectors, Box Model)", "Flexbox & Grid Layouts", "Responsive Media Queries & Mobile-First Design"]},
            {"phase": "Phase 3: JavaScript Programming", "topics": ["Syntax & Data Types", "DOM Manipulation & Events", "Fetch API / Axios / REST integration", "ES6+ Modern Syntax (Arrow functions, Destructuring, Promises, Async/Await)"]},
            {"phase": "Phase 4: Version Control & Tools", "topics": ["Git Basics & Commands", "GitHub/GitLab team workflows", "Package Managers (npm, yarn)", "Vite & Build Bundlers"]},
            {"phase": "Phase 5: Framework Ecosystem (React)", "topics": ["Components & Props", "State Management (useState, useEffect)", "Context API & Custom Hooks", "Router Integration (React Router)", "State Engines (Redux Toolkit, Zustand)"]},
            {"phase": "Phase 6: Advanced Frontend Styles", "topics": ["CSS-in-JS (Styled Components)", "Tailwind CSS", "CSS Modules", "Framer Motion Animations"]},
            {"phase": "Phase 7: Testing & Deploying", "topics": ["Jest & React Testing Library unit checks", "Vercel / Netlify / Firebase deployment", "Web Vitals & Performance Optimization"]}
        ],
    },
    {
        "role": "Backend Developer",
        "description": "Build high-performance, secure, and scalable server-side business logic, database integrations, background task workers, and Web APIs.",
        "steps": [
            {"phase": "Phase 1: Language Specialization", "topics": ["Python (FastAPI, Django)", "JavaScript (Node.js, Express)", "Java (Spring Boot)", "Go / Rust"]},
            {"phase": "Phase 2: Version Control & Hosting", "topics": ["Git and Github workflow", "Command-line scripting", "SSH and VPS configuration"]},
            {"phase": "Phase 3: Database & ORM Integration", "topics": ["SQL Relational Databases (PostgreSQL, MySQL)", "NoSQL Databases (MongoDB, Redis caching)", "ORM/ODM Drivers (SQLAlchemy, Motor, Mongoose)", "Database indexing and Query Optimization"]},
            {"phase": "Phase 4: API Design & Architecture", "topics": ["RESTful Standards", "GraphQL API integrations", "FastAPI Pydantic Schemas", "Authentication (JWT, OAuth2, Session keys)", "CORS and Security Headers"]},
            {"phase": "Phase 5: Async Caching & Queues", "topics": ["Redis Caching layers", "Message Brokers (RabbitMQ, Kafka)", "Celery Async task execution"]},
            {"phase": "Phase 6: Testing & Security", "topics": ["Unit testing (pytest, Jest)", "Security scanning", "Password hashing (Bcrypt, Argon2)"]},
            {"phase": "Phase 7: CI/CD & Cloud Deployments", "topics": ["Docker Containerization", "GitHub Actions CI/CD pipeline", "Deploying to Render, AWS, or GCP"]}
        ],
    },
    {
        "role": "DevOps Engineer",
        "description": "Bridge the gap between software developers and IT operations. Build CI/CD pipelines, containerize architectures, and automate cloud infrastructure.",
        "steps": [
            {"phase": "Phase 1: Operating Systems & Shells", "topics": ["Linux Administration (Ubuntu/Debian)", "Shell Scripting (Bash, Zsh)", "File Systems, Processes, & Resource monitoring"]},
            {"phase": "Phase 2: Networking & Security", "topics": ["IP Addressing & Subnets", "DNS, Ports, HTTP, TCP/UDP protocols", "Firewalls, SSL/TLS Certificates, SSH keys"]},
            {"phase": "Phase 3: Containerization", "topics": ["Docker Containers, Images, & Volumes", "Docker Compose multi-service architecture", "Container security & minimal base images"]},
            {"phase": "Phase 4: Continuous Integration / Continuous Deployment", "topics": ["GitHub Actions pipelines", "Jenkins / GitLab CI", "Build artifact compilation & Docker Hub uploads"]},
            {"phase": "Phase 5: Infrastructure as Code (IaC)", "topics": ["Terraform configuration", "Ansible provisioning & server setups", "AWS / GCP cloud resource automation"]},
            {"phase": "Phase 6: Container Orchestration", "topics": ["Kubernetes (Pods, Deployments, Services)", "Helm Charts packaging", "Minikube local clusters"]},
            {"phase": "Phase 7: Monitoring & Logging", "topics": ["Prometheus metrics collection", "Grafana dashboards monitoring", "ELK Stack (Elasticsearch, Logstash, Kibana)"]}
        ],
    },
    {
        "role": "Data Scientist",
        "description": "Extract valuable business intelligence and construct predictive models from structured and unstructured big datasets.",
        "steps": [
            {"phase": "Phase 1: Math & Statistics Foundation", "topics": ["Linear Algebra & Matrix calculus", "Probability theory (Bayes theorem, Distributions)", "Descriptive & Inferential statistics", "Hypothesis testing (A/B testing, p-values)"]},
            {"phase": "Phase 2: Python Data Engineering Suite", "topics": ["NumPy vector operations", "Pandas DataFrames (Cleaning, Filtering, Aggregation)", "Data visualizations (Matplotlib, Seaborn)"]},
            {"phase": "Phase 3: Machine Learning Models", "topics": ["Supervised Learning (Regression, Classification)", "Unsupervised Learning (K-Means Clustering, PCA)", "Scikit-Learn library usage", "Model Evaluation metrics (MSE, F1-Score, ROC-AUC)"]},
            {"phase": "Phase 4: Deep Learning Foundations", "topics": ["Neural Network architectures", "Backpropagation optimization", "TensorFlow & PyTorch frameworks", "Computer Vision (CNNs) & NLP (Transformers)"]},
            {"phase": "Phase 5: Big Data & Querying", "topics": ["SQL Database advanced querying", "Apache Spark distributed computation", "NoSQL Data Warehouses (Snowflake, BigQuery)"]},
            {"phase": "Phase 6: Data Visualization & BI", "topics": ["Tableau / PowerBI dashboards", "Plotly / Streamlit quick interactive apps"]},
            {"phase": "Phase 7: Model MLOps Deployment", "topics": ["MLflow experiment tracking", "FastAPI ML model wrappers", "Docker containerization & cloud hosting"]}
        ],
    }
]

async def scrape_roadmaps() -> int:
    """Attempts to dynamically scrape roadmap topics from open-source career lists. Falls back cleanly to pre-curated industry sheets."""
    scraped_count = 0
    scraped_data = []
    
    # Target URL: Public web developer roadmap checklist
    target_url = "https://raw.githubusercontent.com/kamranahmedse/developer-roadmap/master/src/data/roadmaps/frontend/roadmap.txt"
    
    try:
        logger.info("Initiating dynamic roadmap checklist scrape...")
        headers = {"User-Agent": get_random_user_agent()}
        
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(target_url, headers=headers)
            
            if response.status_code == 200:
                # Scraped successfully, let's parse a quick custom dynamic structure!
                lines = response.text.split("\n")
                phases = []
                current_phase = {"phase": "Internet Fundamentals", "topics": []}
                
                for line in lines:
                    line = line.strip()
                    if line.startswith("- "):
                        current_phase["topics"].append(line.replace("-", "").strip())
                    elif line.startswith(":") and len(current_phase["topics"]) > 0:
                        phases.append(current_phase)
                        current_phase = {"phase": line.replace(":", "").strip(), "topics": []}
                
                if current_phase["topics"]:
                    phases.append(current_phase)
                
                if phases:
                    scraped_data.append({
                        "role": "Frontend Developer (Live)",
                        "description": "Aggregated live frontend developer checklist from dev roadmap files.",
                        "steps": phases,
                    })
        
        await random_anti_block_delay(0.5, 1.5)
        
    except Exception as e:
        logger.error(f"Live roadmap scrape skipped: {e}. Decoupling to fail-safe database mode.")
        
    # Fail-safe static merge
    if not scraped_data:
        logger.info("Using curated career path roadmaps fallback dataset.")
        scraped_data = CURATED_ROADMAPS
        
    # Save/Upsert to PostgreSQL using ON CONFLICT on unique `role` column
    async with SessionLocal() as session:
        try:
            for roadmap in scraped_data:
                try:
                    stmt = pg_insert(Roadmap).values(
                        role=roadmap["role"],
                        description=roadmap.get("description"),
                        steps=roadmap["steps"],
                    ).on_conflict_do_update(
                        index_elements=["role"],
                        set_={
                            "description": roadmap.get("description"),
                            "steps": roadmap["steps"],
                        }
                    )
                    await session.execute(stmt)
                    scraped_count += 1
                except Exception as db_err:
                    logger.error(f"Failed to record roadmap path: {db_err}")
            
            await session.commit()
        except Exception as commit_err:
            await session.rollback()
            logger.error(f"Failed to commit roadmaps batch: {commit_err}")
            
    logger.info(f"Recorded {scraped_count} career path roadmaps in PostgreSQL.")
    return scraped_count
