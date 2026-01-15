from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# ======================================================
# DATABASE
# ======================================================

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ======================================================
# PASSWORDS (ARGON2)
# ======================================================

pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

# ======================================================
# MODELS
# ======================================================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String, nullable=False)


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    genre = Column(String, nullable=False)
    status = Column(String, nullable=False)
    user_id = Column(Integer, nullable=False)


Base.metadata.create_all(bind=engine)

# ======================================================
# APP
# ======================================================

app = FastAPI()
app.mount(
    "/static",
    StaticFiles(directory=os.path.join(BASE_DIR, "static")),
    name="static"
)
templates = Jinja2Templates(directory="templates")

# ======================================================
# DEPENDENCIES
# ======================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session):
    user_id = request.cookies.get("user_id")
    if not user_id:
        return None
    return db.query(User).filter(User.id == int(user_id)).first()

# ======================================================
# ROUTES
# ======================================================

# ---------- HOME ----------

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# ---------- REGISTER ----------

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse(
        "register.html",
        {"request": request}
    )

@app.post("/register", response_class=HTMLResponse)
def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    if len(username) < 3:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Логін має містити мінімум 3 символи"}
        )

    if len(password) < 6:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Пароль має містити мінімум 6 символів"}
        )

    user = User(
        username=username,
        password=hash_password(password)
    )

    try:
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Такий логін вже існує"}
        )

    return RedirectResponse("/login", status_code=303)

# ---------- LOGIN ----------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login", response_class=HTMLResponse)
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Невірний логін або пароль"}
        )

    response = RedirectResponse("/profile", status_code=303)
    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True,
        samesite="lax"
    )
    return response

# ---------- PROFILE ----------

@app.get("/profile", response_class=HTMLResponse)
def profile(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    games = db.query(Game).filter(Game.user_id == user.id).all()

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user, "games": games}
    )

# ---------- ADD GAME ----------

@app.get("/add-game", response_class=HTMLResponse)
def add_game_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "add_game.html",
        {"request": request}
    )

@app.post("/add-game")
def add_game(
    request: Request,
    title: str = Form(...),
    genre: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    game = Game(
        title=title,
        genre=genre,
        status=status,
        user_id=user.id
    )

    db.add(game)
    db.commit()

    return RedirectResponse("/profile", status_code=303)

# ---------- LOGOUT ----------

@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    return response
