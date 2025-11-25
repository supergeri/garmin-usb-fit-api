# garmin-usb-fit-api

Python FastAPI microservice to generate FIT files for Garmin USB export.

## Local dev

```bash
cd garmin-usb-fit-api
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8095
```


