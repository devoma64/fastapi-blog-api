from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exception_handlers import (
    http_exception_handler,
    request_validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scalar_fastapi import get_scalar_api_reference
from starlette.exceptions import HTTPException as StarletteException

from schemas import PostCreate, PostResponse

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Marvelous Won",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and really fast.",
        "date_posted": "July 22, 2026",
    },
    {
        "id": 2,
        "author": "John Doe",
        "title": "Learning Python",
        "content": "Python makes backend development enjoyable.",
        "date_posted": "July 23, 2026",
    },
    {
        "id": 3,
        "author": "Jane Smith",
        "title": "Why I Love APIs",
        "content": "REST APIs connect applications seamlessly.",
        "date_posted": "July 24, 2026",
    },
]


@app.get("/", include_in_schema=False)
@app.get("/posts", include_in_schema=False)
def index(request: Request):
    title = "Home"
    return templates.TemplateResponse(
        request, "index.html", {"posts": posts, "title": title}
    )


@app.get("/posts/{id}", include_in_schema=False)
def post_page(id: int, request: Request):

    post = next((post for post in posts if post.get("id") == id), None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found"
        )

    title = post["title"][:50]
    return templates.TemplateResponse(
        request, "post.html", {"post": post, "title": title}
    )


@app.get("/api/posts/", response_model=list[PostResponse])
def get_posts():
    return posts


@app.get("/api/posts/{id}", response_model=PostResponse)
def get_post(id: int):
    post = next((post for post in posts if post.get("id") == id), None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )
    return post


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


@app.get("/scalar_docs", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="BLOG | API")
