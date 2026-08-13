# Encryption-System
This is the repository for a morse code encrypted in the pixels of a series of encrypted images, for CSE 220 project of Epshita Jahan and Tafsir Al Nafin.


Workflow:
Browser (React)
   │  POST /api/encrypt (FormData)
   ▼
main.py                → just wires everything up, doesn't run per-request
   │  (app.include_router registered this path at startup)
   ▼
routers/image_router.py     → matches the path+method, unpacks the request
   │  calls encrypt_controller(cover_image, key_image, x, y)
   ▼
controllers/image_controller.py   → the actual orchestration:
   │    1. file_to_array() twice           (services/image_utils.py)
   │    2. store into state                (services/state.py)
   │    3. encrypt_image(...)               (services/crypto.py)
   │    4. array_to_base64() on the result  (services/image_utils.py)
   │    5. wrap it in ImageResponse         (schemas/image_schemas.py)
   ▼
routers/image_router.py     → returns that ImageResponse, FastAPI serializes to JSON
   ▼
Browser (React)              → axios resolves res.data.image, renders <img>


**How to add new stuff:**
Schema first — define the request/response shape in schemas/. For example, EncodeSequenceResponse with frames: list[str] and unit_sequence: list[str]. This forces you to decide the contract before writing logic against it.
Service(s) next — anything reusable that doesn't know about HTTP at all (Morse timing conversion, frame building, key derivation) goes in services/. These functions should be testable by calling them directly in a Python shell, with no FastAPI involved.
Controller — write the orchestration function in controllers/ that calls your new services in the right order and returns the schema object. This is where try/except NotImplementedError and any HTTP-specific error handling (HTTPException) belongs.
Router — add the thinnest possible route handler in routers/, just unpacking the request and calling the controller. No logic here beyond parameter parsing.
Register — if it's a new router file (not just a new route in an existing one), import and app.include_router(...) it in main.py.
Frontend last — once you've smoke-tested the endpoint (same way I did above — call it directly and check status codes), wire up the React side calling it.



**How to Activate:**

cd backend
python3 -m venv venv
source venv/bin/activate      # on Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

cd frontend
npm install
npm run dev