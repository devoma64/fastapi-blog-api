from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import Base, engine


@asynccontextmanager
async def lifespan_handler(lifespan_handler: FastAPI):
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
        yield

        await engine.dispose()
