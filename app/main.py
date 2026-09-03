from fastapi import FastAPI

app = FastAPI(title="Futurisys API")


@app.get("/")
def root():
    return {"status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}