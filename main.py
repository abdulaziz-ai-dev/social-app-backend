from fastapi import FastAPI, Depends
from fastapi.security import OAuth2PasswordRequestForm
from database import engine, Base, SessionLocal
import models
from pydantic import BaseModel
from sqlalchemy.orm import Session
from security import hash_password, verify_password, create_access_token, decode_token


Base.metadata.create_all(bind=engine)


app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



class UserCreate(BaseModel):
    username: str
    email: str
    password: str



@app.post("/users/")
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    new_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hash_password(user.password)
    )   
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id ": new_user.id, "username": new_user.username, "email": new_user.email}



@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        return {"error": "invalid username or password"}

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/me")
def read_me(current_user: str = Depends(decode_token)):
    return {"username": current_user}

class PostCreate(BaseModel):
    content: str

@app.post("/posts")
def create_post(post: PostCreate, current_user: str = Depends(decode_token), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == current_user).first()

    new_post = models.Post(content=post.content, owner_id=user.id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return {"id": new_post.id, "content": new_post.content, "owner_id": new_post.owner_id}



@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    posts = db.query(models.Post).all()
    return posts

@app.get("/posts/{post_id}")
def get_post(post_id: int, db: Session = Depends(get_db)):
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        return {"error": "post not found"}
    return post

