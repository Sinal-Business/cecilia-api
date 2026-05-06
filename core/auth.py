import os
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


TOKEN = os.getenv("TOKEN")
bearer_scheme = HTTPBearer(auto_error=True)

def verify(creds: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    if not TOKEN:
        raise HTTPException(status_code=500, detail="API token not configured")

    if creds.credentials != TOKEN:
        raise HTTPException(status_code=403, detail="Invalid token")

    return True