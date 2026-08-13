from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.image_router import router as image_router

app = FastAPI(title="Two-Factor Image Encryption API")

# Allow the Vite dev server to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
