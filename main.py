from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from routers.adm import router as adm_router
from routers.chatbots import router as chatbots_router
from routers.health import router as health_router
from routers.shopping import router as shopping_router
from routers.validations import router as validations_router


tags_metadata = [
    {
        "name": "General",
        "description": "API for general use"
    },
    {
        "name": "Sinal",
        "description": "API for Sinal data"
    },
    {
        "name": "Harmonia",
        "description": "API for Harmonia data"
    },
    {
        "name": "3M",
        "description": "API for 3M data"
    },
    {
        "name": "Shopping",
        "description": "API for Shopping data"
    },
    {
        "name": "Chatbots",
        "description": "API for chatbot application events"
    },
    {
        "name": "Health",
        "description": "API health checks and infrastructure diagnostics"
    }
]

app = FastAPI(
    title="CECILia API",
    version="2.0.0",
    servers=[{"url": "https://sinalbusiness-cecilia-api.onrender.com"}],
    description="""
API services for Sinal Business.

### Authentication

Send the assigned credential as `Authorization: Bearer TOKEN`.

- `TOKEN` is the primary credential and can access every protected endpoint.
- `TOKEN_SECONDARY` is reserved for the Skeps IA Skill at
  [ia.skeps.com.br](https://ia.skeps.com.br). It can access only the five
  documented read-only Shopping endpoints.
- The Skeps token cannot call `POST`, `PATCH`, or any protected endpoint that
  is not explicitly allowlisted.

Current Skeps allowlist:

- `GET /shopping/flows/hotspot-access`
- `GET /shopping/flows/parking-access`
- `GET /shopping/flows/parking-places`
- `GET /shopping/flows/people-access`
- `GET /shopping/finance/sales`

Skeps IA is the organization-wide AI hub, organized into the Sinal and Caucaia
platforms. New endpoints are denied to its token until they are reviewed and
added to the allowlist.

```http
Authorization: Bearer TOKEN
Content-Type: application/json
```
""",
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url=None
)

@app.get("/docs", include_in_schema=False)
def custom_redoc():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Cecilia API - Documentação"
    )

app.include_router(validations_router)
app.include_router(adm_router)
app.include_router(chatbots_router)
app.include_router(shopping_router)
app.include_router(health_router)
