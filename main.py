from fastapi import FastAPI
from routers.health import router as health_router
from routers.validations import router as validations_router


app = FastAPI(
    title="Cecilia API",
    version="2.0.0"
)

app.include_router(health_router)
app.include_router(validations_router)