from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional

class CardData(BaseModel):
    full_name: str
    phone: str
    email: EmailStr
    website: Optional[HttpUrl] = None
    company: Optional[str] = None
    job_title: Optional[str] = None
