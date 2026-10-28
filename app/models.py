from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class User(BaseModel):
    id: str
    username: str
    full_name: str
    avatar_url: str
    bio: str
    followers_count: int = 0
    following_count: int = 0
    is_verified: bool = False
    is_private: bool = False


class Comment(BaseModel):
    id: str
    post_id: str
    author: User
    text: str
    created_at: str


class Post(BaseModel):
    id: str
    author: User
    image_url: str
    caption: str
    likes_count: int = 0
    comments_count: int = 0
    comments: List[Comment] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: str
    is_liked: bool = False


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    bio: Optional[str] = ""


class CreatePostRequest(BaseModel):
    caption: str
    image_url: str
    tags: Optional[List[str]] = Field(default_factory=list)


class CreateCommentRequest(BaseModel):
    text: str


class Story(BaseModel):
    id: str
    author: User
    media_url: str
    is_seen: bool = False
    created_at: str

