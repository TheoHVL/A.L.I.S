from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def get_status():
    return {"status": "ok"}