# Service A

This is a standalone FastAPI microservice for the `AlgoFlow_AI` project, configured to run on port `8000`.

## Local Setup

### 1. Create and Activate Virtual Environment
```bash
python -m venv venv
```

* **Windows (PowerShell)**:
  ```powershell
  .\venv\Scripts\Activate.ps1
  ```
* **macOS/Linux**:
  ```bash
  source venv/bin/activate
  ```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run Development Server
```bash
uvicorn app.main:app --reload --port 8000
```

---

## API Endpoints

* **Root Welcome**: [http://localhost:8000/](http://localhost:8000/)
* **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
* **Interactive OpenAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Alternative Redoc Docs**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
