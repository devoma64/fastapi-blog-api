from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteException

import models
from database import Base, engine, get_db
from schemas import (
    PostCreate,
    PostResponse,
    PostUpdate,
    UserCreate,
    UserResponse,
    UserUpdate,
)

Base.metadata.create_all(bind=engine)

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/media", StaticFiles(directory="media"), name="media")

templates = Jinja2Templates(directory="templates")


@app.get("/", include_in_schema=False, name="index")
@app.get("/posts", include_in_schema=False, name="posts")
def index(request: Request, db: Annotated[Session, Depends(get_db)]):

    result = db.execute(select(models.Post))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request, "index.html", {"posts": posts, "title": "Home"}
    )


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(post_id: int, request: Request, db: Annotated[Session, Depends(get_db)]):

    results = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = results.scalars().first()

    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post": post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")


@app.get(
    "/users/{user_id}/posts",
    include_in_schema=False,
    response_model=list[PostResponse],
    name="user_posts",
)
def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User not found."
        )

    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )


@app.get("/api/users", response_model=list[UserResponse])
def get_users(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User))
    users = result.scalars().all()
    return users


@app.post(
    "/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(
        select(models.User).where(models.User.username == user.username)
    )
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exist."
        )

    result = db.execute(select(models.User).where(models.User.email == user.email))
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists."
        )

    new_user = models.User(username=user.username, email=user.email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))

    user = result.scalars().first()
    if user:
        return user

    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="user not found.")


@app.patch("/api/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int, user_update: UserUpdate, db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    if user_update.username is None and user_update.username != user.username:
        result = db.execute(
            select(models.User).where(models.User.username == user_update.username)
        )
        existing_user = result.scalars().first()

        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already registered",
            )

    if user_update.email is None and user_update.email != user.email:
        result = db.execute(
            select(models.User).where(models.User.email == user_update.email)
        )

        existing_email = result.scalars().first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered.",
            )

    if user_update.username is not None:
        user.username = user_update.username

    if user_update.email is not None:
        user.email = user_update.email

    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    db.commit()
    db.refresh(user)

    return user 


@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )

    db.delete(user)
    db.commit()


@app.get("/api/posts/", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.post(
    "/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED
)
def create_post(post: PostCreate, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )
    new_post = models.Post(
        title=post.title,
        content=post.content,
        user_id=post.user_id,
    )

    db.add(new_post)
    db.commit()
    db.refresh(new_post)

    return new_post


@app.get("/api/posts/{post_id}", response_model=PostResponse, name="post")
def get_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.User.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )

    return post


@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int, updated_data: PostCreate, db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )

    if updated_data.user_id != post.user_id:
        result = db.execute(
            select(models.User).where(models.User.id == updated_data.user_id)
        )
        user = result.scalars().first()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
            )

    post.title = updated_data.title
    post.content = updated_data.content
    post.user_id = updated_data.user_id

    db.commit()
    db.refresh(post)

    return post


@app.patch("/api/posts/{post_id}")
def update_post_partial(
    post_id: int, updated_data: PostUpdate, db: Annotated[Session, Depends(get_db)]
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )

    post_update = updated_data.model_dump(exclude_unset=True)
    for field, value in post_update.items():
        setattr(post, field, value)

    db.commit()
    db.refresh(post)

    return post


@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )

    db.delete(post)
    db.commit()


@app.exception_handler(StarletteException)
def general_http_exception_handler(request: Request, exception: StarletteException):
    if request.url.path.startswith("/api"):
        return http_exception_handler(request, exception)

    message = (
        exception.detail or "An error occured. Please check your request and try again."
    )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )


@app.exception_handler(RequestValidationError)
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )
