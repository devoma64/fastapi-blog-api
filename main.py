from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from scalar_fastapi import get_scalar_api_reference

app = FastAPI()

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


@app.get("/", response_class=HTMLResponse)
@app.get("/posts", response_class=HTMLResponse)
def ge_posts():
    return f"<h1>{posts[0]['title']}</h1>"


@app.get("/scalar_docs", include_in_schema=False)
def get_scalar_docs():
    return get_scalar_api_reference(openapi_url=app.openapi_url, title="BLOG | API")
