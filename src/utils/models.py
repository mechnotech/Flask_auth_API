import datetime
from typing import Optional

import orjson
from pydantic import BaseModel, EmailStr


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode('utf-8')


class AdvancedJsonModel(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class OAuthProviderSet(AdvancedJsonModel):
    oauth_provider: str
    request_code: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None


class LoginSet(AdvancedJsonModel):
    login: str
    password: str


class UserSet(LoginSet):
    email: EmailStr


class ProfileSet(AdvancedJsonModel):
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[list]
    bio: Optional[str]


class LogSet(AdvancedJsonModel):
    info: str
    status: str
    created_at: datetime.datetime


class RoleSet(AdvancedJsonModel):
    role: str


class RoleUser(RoleSet):
    user: str
