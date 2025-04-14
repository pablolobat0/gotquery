from fastapi import APIRouter, HTTPException, status
from app.schemas.query import Query

from app.services.query import get_query_response


query_router = APIRouter()


@query_router.post("/query", response_model=list[Query], status_code=status.HTTP_200_OK)
async def get_response(query: Query):
    try:
        return await get_query_response(query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
