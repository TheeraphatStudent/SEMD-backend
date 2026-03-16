from pydantic import BaseModel, Field
from typing import TypeVar, Generic, List, Optional
from fastapi import Query
from math import ceil

T = TypeVar('T')


class PaginationParams:
    def __init__(
        self,
        page: int = Query(1, ge=1, description='Page number (1-indexed)'),
        page_size: int = Query(
            20, ge=1, le=100, description='Number of items per page'),
        sort_by: Optional[str] = Query(None, description='Field to sort by'),
        sort_order: str = Query(
            'desc', regex='^(asc|desc)$', description='Sort order (asc or desc)')
    ):
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class PaginationMeta(BaseModel):
    page: int = Field(..., description='Current page number')
    page_size: int = Field(..., description='Number of items per page')
    total_items: int = Field(..., description='Total number of items')
    total_pages: int = Field(..., description='Total number of pages')
    has_next: bool = Field(..., description='Whether there is a next page')
    has_prev: bool = Field(..., description='Whether there is a previous page')


class PaginatedResponse(BaseModel, Generic[T]):
    status: int = Field(200, description='Response status code')
    message: str = Field('Success', description='Response message')
    data: List[T] = Field(default_factory=list, description='List of items')
    pagination: PaginationMeta = Field(..., description='Pagination metadata')


def create_pagination_meta(
    page: int,
    page_size: int,
    total_items: int
) -> PaginationMeta:
    total_pages = ceil(total_items / page_size) if page_size > 0 else 0
    return PaginationMeta(
        page=page,
        page_size=page_size,
        total_items=total_items,
        total_pages=total_pages,
        has_next=page < total_pages,
        has_prev=page > 1
    )


def paginate_list(
    items: List[T],
    page: int,
    page_size: int
) -> tuple[List[T], PaginationMeta]:
    total_items = len(items)
    offset = (page - 1) * page_size
    paginated_items = items[offset:offset + page_size]
    meta = create_pagination_meta(page, page_size, total_items)
    return paginated_items, meta
