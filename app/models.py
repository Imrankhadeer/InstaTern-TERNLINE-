from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class User(BaseModel):
    id: str
    username: str
    full_name: str
    avatar_url: str
    bio: str = ""
    website: str = ""
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    is_verified: bool = False
    is_private: bool = False
    is_following: bool = False
    role: str = "user"


class UserProfile(User):
    posts: List["Post"] = Field(default_factory=list)
    saved_posts: List["Post"] = Field(default_factory=list)


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
    saves_count: int = 0
    comments: List[Comment] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    created_at: str
    is_liked: bool = False
    is_saved: bool = False


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


class Notification(BaseModel):
    id: str
    recipient: str
    sender: User
    type: str  # like, comment, follow, message
    post_id: Optional[str] = None
    text: str
    created_at: str
    is_read: bool = False


class ActivityAnalytics(BaseModel):
    total_posts: int
    total_likes_received: int
    total_comments_received: int
    followers_count: int
    following_count: int
    engagement_rate: float
    top_tags: List[Dict[str, Any]] = Field(default_factory=list)


# Requests / Responses
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    full_name: str
    bio: Optional[str] = ""
    website: Optional[str] = ""


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
    website: Optional[str] = None
    avatar_url: Optional[str] = None
    is_private: Optional[bool] = None


class SearchFilter(BaseModel):
    q: str
    entity_type: Optional[str] = "all"  # all, users, posts, tags
    sort_by: Optional[str] = "recent"  # recent, popular
    limit: Optional[int] = 20
