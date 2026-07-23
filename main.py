from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from scalar_fastapi import get_scalar_api_reference

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Marvelous Won",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and really fast.",
        "dated_posted": "July 22, 2026",
    },
    {
        "id": 2,
        "author": "John Doe",
        "title": "Learning Python",
        "content": "Python makes backend development enjoyable.",
        "dated_posted": "July 23, 2026",
    },
    {
        "id": 3,
        "author": "Jane Smith",
        "title": "Why I Love APIs",
        "content": "REST APIs connect applications seamlessly.",
        "dated_posted": "July 24, 2026",
    },
]


@app.get("/", include_in_schema=False)
@app.get("/posts", include_in_schema=False)
def index(request: Request):
    return templates.TemplateResponse(
        request, "index.html", {"posts": posts, "title": "Home"}
    )


@app.get("/api/posts")
def get_posts():
    return posts


@app.get("/api/posts/{id}")
def get_post(id: int):
    post = next((post for post in posts if post.get("id") == id), None)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Post not found."
        )
    return post


@app.get("/scalar_docs", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="BLOG | API")
