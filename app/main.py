from fastapi import FastAPI, APIRouter
from app.routes.query import query_router


app = FastAPI()

router = APIRouter()

router.include_router(query_router)

app.include_router(router)
