
from contextlib import asynccontextmanager

from fastapi import FastAPI

from database import Base, engine
import models

from routers.users import router as users_router
from routers.products import router as products_router
from routers.orders import router as orders_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create missing tables. The MySQL database must already exist.
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Mini E-Commerce API",
    description="E-commerce backend using FastAPI, Python, and MySQL",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(users_router)
app.include_router(products_router)
app.include_router(orders_router)


@app.get("/")
def home():
    return {
        "message": "Mini E-Commerce API is running",
        "docs": "/docs",
    }
