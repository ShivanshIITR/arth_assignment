from fastapi import Query

from app.schemas.common import PaginationParams


def pagination_params(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> PaginationParams:
    return PaginationParams(page=page, page_size=page_size)


def offset_for(params: PaginationParams) -> int:
    return (params.page - 1) * params.page_size
