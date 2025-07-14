# models.py
from sqlmodel import SQLModel, Field
from typing import Optional
import datetime

class LMSPlatform(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    issuer: str
    client_id: str
    auth_login_url: str
    deployment_id: str
    jwks_url: Optional[str] = None  # <-- novo campo

class LTIUserLaunch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    course: str
    roles: str
    issuer: str
    raw_payload: str
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)