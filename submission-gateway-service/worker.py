import os
import json
import asyncio
import aio_pika
import requests
from dotenv import load_dotenv
from database import connect_to_mongo, close_mongo_connection, get_db
from models import SubmissionStatus

load_dotenv()

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
RABBITMQ_QUEUE = os.getenv("RABBITMQ_QUEUE", "submissions")
JDOODLE_CLIENT_ID = os.getenv("JDOODLE_CLIENT_ID")
JDOODLE_CLIENT_SECRET = os.getenv("JDOODLE_CLIENT_SECRET")
JDOODLE_API_URL = "https://api.jdoodle.com/v1/execute"

async def execute_on_jdoodle(source_code: str, language: str, stdin: str):
    # Map your internal language_id to JDoodle's language and versionIndex
    # This is a simple mapping, you may need to expand it based on your needs
    language_map = {
        "python": {"language": "python3", "versionIndex": "4"},
        "java": {"language": "java", "versionIndex": "4"},
        "cpp": {"language": "cpp17", "versionIndex": "0"},
        # Add more as needed
    }
    
    lang_config = language_map.get(language.lower(), {"language": language, "versionIndex": "0"})

    payload = {
        "clientId": JDOODLE_CLIENT_ID,
        "clientSecret": JDOODLE_CLIENT_SECRET,
        "script": source_code,
        "language": lang_config["language"],
        "versionIndex": lang_config["versionIndex"],
        "stdin": stdin
    }

    # Note: Using synchronous requests here for simplicity in the worker. 
    # For a high throughput system, aiohttp should be used.
    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(None, lambda: requests.post(JDOODLE_API_URL, json=payload))
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": response.text, "statusCode": response.status_code}


async def process_message(message: aio_pika.IncomingMessage):
    async with message.process():
        body = message.body.decode()
        print(f"Received message: {body}")
        
        try:
            data = json.loads(body)
            submission_id = data.get("_id") or data.get("id")
            
            if not submission_id:
                print("No submission ID found in message. Skipping.")
                return

            db = get_db()
            
            # Update status to PROCESSING
            await db["submissions"].update_one(
                {"_id": submission_id},
                {"$set": {"status": SubmissionStatus.PROCESSING.value}}
            )

            source_code = data.get("source_code", "")
            language_id = data.get("language_id", "python")
            test_cases = data.get("test_cases", [])
            expected_outputs = data.get("expected_outputs", [])

            results = []
            all_passed = True
            
            # If there are test cases, run them against JDoodle
            if test_cases:
                for idx, test_case in enumerate(test_cases):
                    result = await execute_on_jdoodle(source_code, language_id, test_case)
                    
                    # Basic comparison logic
                    passed = False
                    output = result.get("output", "")
                    
                    if expected_outputs and idx < len(expected_outputs):
                        # Simple exact match (in reality, you'd want to trim whitespace etc)
                        expected = expected_outputs[idx]
                        passed = output.strip() == expected.strip()
                    
                    if not passed and expected_outputs:
                        all_passed = False
                    
                    results.append({
                        "test_case": test_case,
                        "expected": expected_outputs[idx] if expected_outputs and idx < len(expected_outputs) else None,
                        "actual": output,
                        "passed": passed,
                        "memory": result.get("memory"),
                        "cpuTime": result.get("cpuTime"),
                        "error": result.get("error")
                    })
            else:
                # No test cases, just run the code
                result = await execute_on_jdoodle(source_code, language_id, "")
                results.append({
                    "actual": result.get("output", ""),
                    "memory": result.get("memory"),
                    "cpuTime": result.get("cpuTime"),
                    "error": result.get("error")
                })

            final_status = SubmissionStatus.COMPLETED.value
            # If you want to mark FAILED when code doesn't compile or execution fails
            if any("error" in r and r["error"] for r in results):
                final_status = SubmissionStatus.FAILED.value

            # Update MongoDB with results
            await db["submissions"].update_one(
                {"_id": submission_id},
                {
                    "$set": {
                        "status": final_status,
                        "results": results
                    }
                }
            )
            print(f"Processed submission {submission_id} with status {final_status}")

        except Exception as e:
            print(f"Error processing message: {e}")
            # Depending on error, we could nack the message or let it be acked and mark FAILED in DB.
            # Here it is acked by the context manager, but we should handle DB update if possible.


async def main():
    await connect_to_mongo()
    
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    
    # Set prefetch count to 1 for fair dispatch
    await channel.set_qos(prefetch_count=1)
    
    queue = await channel.declare_queue(RABBITMQ_QUEUE, durable=True)
    
    print("Worker listening for messages. To exit press CTRL+C")
    
    await queue.consume(process_message)
    
    try:
        # Keep the connection open
        await asyncio.Future()
    finally:
        await connection.close()
        await close_mongo_connection()

if __name__ == "__main__":
    asyncio.run(main())
