## AI Product Tagging (Streamlit + FastAPI)

This project tags messy product text into a small taxonomy (category/brand/subcategory) using OpenAI.

### Setup (Windows PowerShell)

```powershell
cd "d:\THAT I CAN\ai"
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# edit .env and set your key
```

### Run the project

- **Run everything (recommended)**:

```powershell
.\run_project.ps1 -Install
```

- **Or run individually**:

```powershell
# UI
streamlit run app.py
```

```powershell
# API
uvicorn api:app --reload
```

### URLs

- **UI**: `http://localhost:8501`
- **API docs**: `http://127.0.0.1:8000/docs`

### Notes

- `.env` is ignored by git (your API key won’t be committed).
