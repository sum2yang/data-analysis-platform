from pydantic import BaseModel

__all__ = ["PaginatedResponse", "MessageResponse"]


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    page_size: int

    @property
    def has_next(self) -> bool:
        return (self.page * self.page_size) < self.total


class MessageResponse(BaseModel):
    message: str
