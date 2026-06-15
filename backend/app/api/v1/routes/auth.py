from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import encrypt
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["auth"])

SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/classroom.courses.readonly",
    "https://www.googleapis.com/auth/classroom.coursework.me",
    "https://www.googleapis.com/auth/classroom.coursework.students",
    "https://www.googleapis.com/auth/drive.file",
]


def _build_flow() -> Flow:
    return Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        },
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )


@router.get("/google")
def login_google(request: Request):
    flow = _build_flow()
    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url)


@router.get("/callback")
def oauth_callback(request: Request, code: str, state: str, db: Session = Depends(get_db)):
    if request.session.get("oauth_state") != state:
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    flow = _build_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials

    user_info_svc = build("oauth2", "v2", credentials=credentials)
    user_info = user_info_svc.userinfo().get().execute()

    user = db.query(User).filter(User.google_id == user_info["id"]).first()
    if user:
        user.access_token_enc = encrypt(credentials.token)
        if credentials.refresh_token:
            user.refresh_token_enc = encrypt(credentials.refresh_token)
        user.token_expiry = credentials.expiry
    else:
        user = User(
            google_id=user_info["id"],
            email=user_info["email"],
            display_name=user_info.get("name", ""),
            access_token_enc=encrypt(credentials.token),
            refresh_token_enc=encrypt(credentials.refresh_token) if credentials.refresh_token else None,
            token_expiry=credentials.expiry,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    request.session["user_id"] = user.id
    return RedirectResponse(url=settings.FRONTEND_URL)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out"}


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "email": user.email, "display_name": user.display_name}
