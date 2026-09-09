from pydantic import BaseModel


class ProgressCreate(BaseModel):
    course_id: int
    status: str
    percentage: float
    score: float | None = None


class ProgressResponse(ProgressCreate):
    id: int
    user_id: int

    class Config:
        from_attributes = True