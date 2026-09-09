from pydantic import BaseModel


class CourseCreate(BaseModel):
    title: str
    description: str | None = None
    skill_id: int
    difficulty: str
    duration: str
    source: str
    igot_url: str | None = None


class CourseResponse(CourseCreate):
    id: int

    class Config:
        from_attributes = True