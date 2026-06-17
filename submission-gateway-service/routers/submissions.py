from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from models import RunRequest, SubmitRequest, Submission, SubmissionStatus
from database import get_db
from broker import publish_submission
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/submissions",
    tags=["submissions"]
)

@router.post("/run", response_model=dict, status_code=202)
async def run_code(request: RunRequest):
    """
    User runs code -> passed to backend along with sample test case and answers
    """
    submission = Submission(
        type="run",
        source_code=request.source_code,
        language_id=request.language_id,
        test_cases=request.test_cases,
        expected_outputs=request.expected_outputs,
        status=SubmissionStatus.PENDING
    )

    db = get_db()
    # Save to MongoDB
    await db["submissions"].insert_one(submission.model_dump(by_alias=True))

    # Publish event to RabbitMQ
    try:
        await publish_submission(submission)
    except Exception as e:
        logger.error(f"Failed to publish to broker: {e}")
        # In a real system, you might want to retry or handle this gracefully.
        # But we still return 202 to the user as ingestion accepted it.
        # Could also set status to FAILED in DB if broker is completely down.

    return {"message": "Run request accepted", "submission_id": submission.id}

@router.post("/submit", response_model=dict, status_code=202)
async def submit_code(request: SubmitRequest):
    """
    User submits code -> passed to backend -> hidden test cases are fetched from mongodb
    """
    db = get_db()
    
    # Fetch hidden test cases from MongoDB (mocking the collection 'problems')
    problem = await db["problems"].find_one({"_id": request.problem_id})
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    test_cases = problem.get("hidden_test_cases", [])
    expected_outputs = problem.get("hidden_expected_outputs", [])

    submission = Submission(
        type="submit",
        source_code=request.source_code,
        language_id=request.language_id,
        problem_id=request.problem_id,
        test_cases=test_cases,
        expected_outputs=expected_outputs,
        status=SubmissionStatus.PENDING
    )

    # Save to MongoDB
    await db["submissions"].insert_one(submission.model_dump(by_alias=True))

    # Publish event to RabbitMQ
    try:
        await publish_submission(submission)
    except Exception as e:
        logger.error(f"Failed to publish to broker: {e}")

    return {"message": "Submit request accepted", "submission_id": submission.id}
