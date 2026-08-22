from fastapi import FastAPI

app = FastAPI(
    title="AI Document Intelligence",
    description="AI-powered document processing and analysis system",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "AI Document Intelligence API is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }