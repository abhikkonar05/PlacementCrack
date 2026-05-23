# PlacementCrack

PlacementCrack is a full-stack placement preparation platform for students. It includes OTP-based registration, login, a student dashboard, role-based preparation tracks, coding tests, AI-style mock interviews, resume ATS scoring, and scraped job/internship discovery.

## Tech Stack

- Frontend: React, TypeScript, Vite, lucide-react
- Backend: Python, FastAPI, MongoDB/Motor
- AI evaluation: Hugging Face Inference API when `HUGGINGFACE_API_TOKEN` is configured, Gemini optional, local evaluators as fallback
- Jobs: WeWorkRemotely scraping with cache and role filtering
- Auth: JWT + OTP email verification

## Local Setup

1. Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

2. Frontend

```bash
cd frontend
copy .env.example .env
npm install
npm run dev
```

For local frontend development, set:

```env
VITE_API_URL=http://localhost:8000
```

## Deployment

Backend can be deployed on Vercel from the `backend` folder using `backend/vercel.json`. Configure these environment variables in Vercel:

- `MONGODB_URI`
- `JWT_SECRET_KEY`
- `DEVELOPER_MODE=false`
- `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM_EMAIL` for real OTP emails
- `HUGGINGFACE_API_TOKEN`, `HUGGINGFACE_MODEL_ID`, and `HUGGINGFACE_ASR_MODEL_ID` for Hugging Face-generated questions, answer scoring, and voice transcription
- `GEMINI_API_KEY` optional secondary provider for AI-generated interview scoring

Frontend can be deployed on Vercel from the `frontend` folder. Configure:

- `VITE_API_URL=https://your-backend-domain`

## Production Notes

- Use MongoDB Atlas for hosted database access.
- Use a real SMTP app password for OTP emails.
- Keep `JWT_SECRET_KEY` private and long.
- The coding sandbox currently supports Python submissions only.
- The interview module works without external AI keys, but a Hugging Face token enables model-generated questions and stronger answer feedback.
