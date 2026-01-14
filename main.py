from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from passlib.context import CryptContext

# ================= DATABASE =================

DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# ================= SECURITY =================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str):
    return pwd_context.verify(password, hashed)

# ================= MODEL =================

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)

Base.metadata.create_all(bind=engine)

# ================= APP =================

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# ================= DEPENDENCIES =================

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

# ================= ROUTES =================

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

@app.post("/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = User(
        username=username,
        password=hash_password(password)
    )

    try:
        db.add(user)
        db.commit()
    except IntegrityError:
        db.rollback()
        return HTMLResponse(
            "Користувач вже існує <a href='/register'>Назад</a>",
            status_code=400
        )

    return RedirectResponse("/login", status_code=303)

# ---------- LOGIN ----------

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(
        "login.html",
        {"request": request}
    )

@app.post("/login")
def login(
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == username).first()

    if not user or not verify_password(password, user.password):
        return HTMLResponse(
            "Невірний логін або пароль <a href='/login'>Назад</a>",
            status_code=400
        )

    response = RedirectResponse("/profile", status_code=303)
    response.set_cookie(
        key="user_id",
        value=str(user.id),
        httponly=True
    )
    return response

# ---------- PROFILE (PROTECTED) ----------

@app.get("/profile", response_class=HTMLResponse)
def profile(
    request: Request,
    db: Session = Depends(get_db)
):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse("/login", status_code=303)

    return templates.TemplateResponse(
        "profile.html",
        {"request": request, "user": user}
    )

# ---------- LOGOUT ----------

@app.get("/logout")
def logout():
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("user_id")
    return response
