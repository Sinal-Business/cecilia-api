from fastapi import APIRouter
from fastapi.responses import FileResponse


router = APIRouter()

@router.get("/", include_in_schema=False)
def read_root():
    return {"status": "API on air"}

@router.get("/openapi.yaml", include_in_schema=False)
def get_openapi():
    return FileResponse("openapi.yaml")

@router.get("/.well-known/ai-plugin.json", include_in_schema=False)
def serve_ai_plugin():
    return FileResponse(".well-known/ai-plugin.json")