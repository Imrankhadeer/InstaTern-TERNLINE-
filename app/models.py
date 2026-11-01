from typing import List, Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    username: str
    full_name: str
    avatar_url: str
    bio: str = ""
    followers_count: int = 0
    following_count: int = 0
    is_verified: bool = False
    is_private: bool = False
    role: str = "user"


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
    caption: str = ""
    likes_count: int = 0
    comments_count: int = 0
    comments: List[Comment] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: str
    is_liked: bool = False


class Story(BaseModel):
    id: str
    author: User
    media_url: str
    created_at: str


class DirectMessage(BaseModel):
    id: str
    conversation_id: str
    sender: str
    recipient: str
    text: str
    timestamp: str


class Conversation(BaseModel):
    id: str
    participants: List[str]
    last_message: str
    last_updated: str
    messages: List[DirectMessage] = Field(default_factory=list)


# Requests / Responses
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


class SendMessageRequest(BaseModel):
    recipient: str
    text: str


class CreateStoryRequest(BaseModel):
    media_url: str


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
