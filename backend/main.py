"""
FastAPI entry point.

Routes:
    GET  /api/health
    POST /api/encrypt   (cover image + secret key image + password)
    POST /api/decrypt-with-key-images   (message_id + key image + password)

The DRPE engine lives in services/drpe.py. The Phase 2 Morse/text
extension point is services/encoding/ (currently a placeholder package
of import-safe NotImplementedError stubs).
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.image_router import router as image_router
from routers.text_router import router as text_router

app = FastAPI(title="DRPE Phase 1 Demo API")

# Allow the Vite dev server to call this API from the browser.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router)
app.include_router(text_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}
