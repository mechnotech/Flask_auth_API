from typing import Optional

import orjson

from pydantic import BaseModel, EmailStr


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode('utf-8')


class AdvancedJsonModel(BaseModel):
    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class LoginSet(AdvancedJsonModel):
    login: str
    password: str


class UserSet(LoginSet):
    email: EmailStr


class ProfileSet(AdvancedJsonModel):
    first_name: Optional[str]
    last_name: Optional[str]
    role: Optional[str]
    bio: Optional[str]
