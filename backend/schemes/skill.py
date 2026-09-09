from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    category: str
    description: str | None = None


class SkillResponse(SkillCreate):
    id: int

    class Config:
        from_attributes = True