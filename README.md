# AlgoFlow_AI

A microservices-based project structured as a monorepo containing two independent FastAPI services: `service_a` and `service_b`.

## Repository Structure

```
AlgoFlow_AI/
├── .gitignore
├── README.md
└── services/
    ├── service_a/         # Service A running on port 8000
    │   ├── app/
    │   └── requirements.txt
    └── service_b/         # Service B running on port 8001
        ├── app/
        └── requirements.txt
```

---

## Local Setup & Development

Each service runs independently in its own directory and environment. To set them up locally, follow these steps for each service.

### 1. Set Up Service A (Port 8000)

```bash
# Navigate to the service_a folder
cd services/service_a

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --port 8000
```

Once running, you can access:
* Service API: [http://localhost:8000](http://localhost:8000)
* Health Check: [http://localhost:8000/health](http://localhost:8000/health)
* Interactive Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### 2. Set Up Service B (Port 8001)

```bash
# Navigate to the service_b folder
cd services/service_b

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the service
uvicorn app.main:app --reload --port 8001
```

Once running, you can access:
* Service API: [http://localhost:8001](http://localhost:8001)
* Health Check: [http://localhost:8001/health](http://localhost:8001/health)
* Interactive Docs: [http://localhost:8001/docs](http://localhost:8001/docs)

---

## Architecture Overview

* **FastAPI**: Used for creating high-performance, asynchronous REST APIs.
* **Pydantic Settings**: Used to manage environment configurations for each microservice independently.
* **Separation of Concerns**: Each service is self-contained under `services/`, allowing for easy migration to separate repositories or Docker containers in the future.
