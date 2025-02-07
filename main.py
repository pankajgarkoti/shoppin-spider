from fastapi import FastAPI
from src.api.crud import _router

app = FastAPI()
app.include_router(_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
