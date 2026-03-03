from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from tagging import tag_product


app = FastAPI(title="Product Tagging API", version="1.0.0")


class TagRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Unstructured product text")


class BatchTagRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/tag")
def tag(req: TagRequest) -> Dict[str, Any]:
    try:
        return tag_product(req.text)
    except Exception as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.post("/tag/batch")
def tag_batch(req: BatchTagRequest) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    for t in req.texts:
        try:
            results.append(tag_product(t))
        except Exception as e:
            results.append(
                {
                    "normalized_text": t,
                    "taxonomy": {"category": None, "subcategory": None, "brand": None},
                    "attributes": {},
                    "confidence": 0.0,
                    "error": str(e),
                }
            )
    return {"results": results}

