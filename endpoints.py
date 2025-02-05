from fastapi import FastAPI, Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from .models import Users, Shorten
from .schemas import UserCreate, User, Token, TokenData, ShortenCreate, Shorten as ShortenSchema
from .database import get_db
from .utility import shorten_url
from fastapi.responses import RedirectResponse

app = FastAPI()
router = APIRouter()

# Security configurations
SECRET_KEY = "your-secret-key-keep-it-secret"  # In production, use proper secret management
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Security utilities
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = db.query(Users).filter(Users.username == token_data.username).first()
    if user is None:
        raise credentials_exception
    return user

# User endpoints
@router.post("/users/", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(Users).filter(Users.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    db_user = Users(
        email=user.email,
        username=user.username,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(Users).filter(Users.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# URL shortening endpoints
@router.post("/shorten/", response_model=ShortenSchema)
async def create_short_url(
    url_data: ShortenCreate,
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    expires_at = datetime.utcnow() + timedelta(hours=24)
    short_url = shorten_url(str(url_data.long_url), expires_at)  # Adjust if your utility function requires this
    db_short = db.query(Shorten).filter(Shorten.short_url == short_url).first()
    while db_short:
        short_url = shorten_url(str(url_data.long_url), expires_at)
        db_short = db.query(Shorten).filter(Shorten.short_url == short_url).first()
    
    db_url = Shorten(
        long_url=str(url_data.long_url),
        short_url=short_url,
        expires_at=expires_at,
        user_id=current_user.id
    )
    db.add(db_url)
    db.commit()
    db.refresh(db_url)
    return db_url

@router.get("/{short_code}")
async def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    url = db.query(Shorten).filter(Shorten.short_url.endswith(short_code)).first()
    if not url:
        raise HTTPException(status_code=404, detail="URL not found")
    if datetime.utcnow() > url.expires_at:
        raise HTTPException(status_code=410, detail="URL has expired")
    return RedirectResponse(url=url.long_url)

@router.get("/urls/", response_model=List[ShortenSchema])
async def get_urls(
    current_user: Users = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return db.query(Shorten).filter(Shorten.user_id == current_user.id).all()