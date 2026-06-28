from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from k8s_service.app.api.kubernetes import k8s_router
from shared.database.session import get_db
from shared.security.jwt import create_access_token
from shared.security.password import verify_password

app = FastAPI(
    title="Kubernetes Service",
    description="Kubernetes cluster management API for AI DevOps Orchestrator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(k8s_router, prefix="/k8s", tags=["Kubernetes"])


# ── Auth token endpoint ───────────────────────────────────────────────────────
# This is what Swagger's "Authorize" form POSTs to when using username/password.
# It validates credentials against the shared users table and returns a JWT.

@app.post(
    "/token",
    tags=["Auth"],
    summary="Get access token (username = email)",
    response_description="JWT access token for use on all /k8s/* endpoints",
)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """
    Standard OAuth2 Password flow.

    - **username**: your registered email address
    - **password**: your password

    Returns a `Bearer` JWT valid for 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`).
    """
    # Import here to avoid circular imports at module load time
    from shared.database.base import Base  # noqa: F401 — ensure models are mapped
    from sqlalchemy import text

    # Query user by email (username field holds the email in OAuth2 form)
    result = db.execute(
        text("SELECT id, email, password, role FROM users WHERE email = :email"),
        {"email": form_data.username},
    ).fetchone()

    if result is None or not verify_password(form_data.password, result.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token({"sub": result.email, "role": result.role})

    return {"access_token": access_token, "token_type": "bearer"}


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    return {"service": "k8s-service", "message": "Kubernetes Service Running", "docs": "/docs"}