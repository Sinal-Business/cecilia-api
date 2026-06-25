from fastapi import FastAPI
from fastapi.openapi.docs import get_redoc_html
from routers.adm import router as adm_router
from routers.health import router as health_router
from routers.validations import router as validations_router


tags_metadata = [
    {
        "name": "General",
        "description": "API for general use"
    },
    {
        "name": "Adm",
        "description": "API for administrations use"
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
        "name": "Health",
        "description": "API health checks and infrastructure diagnostics"
    }
]

app = FastAPI(
    title="CECILia API",
    version="2.0.0",
    description="""
API de serviços da Sinal Business

### ⚠️ Autenticação:  

Para utilizar os recursos é necessário se autenticar utilizando o TOKEN com as credenciais fornecidas.  

> Se você não tem esse acesso, contate o time técnico responsável  

As credenciais devem ser informadas no header `Authorization` da requisição:

```http
Authorization: Bearer TOKEN
Content-Type: application/json
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

app.include_router(health_router)
app.include_router(validations_router)
app.include_router(adm_router)
