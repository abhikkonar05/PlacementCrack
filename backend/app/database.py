from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger("app.database")

# Initialize motor client
client = AsyncIOMotorClient(settings.MONGODB_URI)
# Extract database from connection string, or fallback to 'placementcrack'
db = client.get_database("placementcrack")

# Collections definition
users_collection = db["users"]
otps_collection = db["otps"]
login_keys_collection = db["login_keys"]
submissions_collection = db["submissions"]
interviews_collection = db["interviews"]
ats_checks_collection = db["ats_checks"]
dsa_problems_collection = db["dsa_problems"]
aptitude_questions_collection = db["aptitude_questions"]
opportunities_collection = db["opportunities"]
interview_questions_collection = db["interview_questions"]

async def check_db_connection():
    try:
        # Ping database to verify connection
        await client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
        
        # Ensure unique indexes on email
        await users_collection.create_index("email", unique=True, sparse=True)
        await otps_collection.create_index("email", unique=True, sparse=True)
        await login_keys_collection.create_index("email", unique=True, sparse=True)
        
        return True
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        return False
