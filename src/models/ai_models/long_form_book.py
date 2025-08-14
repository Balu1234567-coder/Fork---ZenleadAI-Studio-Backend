from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum

class BookLength(str, Enum):
    SHORT = "short"  # 50-100 pages
    STANDARD = "standard"  # 150-250 pages  
    EXTENDED = "extended"  # 300-400 pages
    EPIC = "epic"  # 500+ pages

class BookGenre(str, Enum):
    NON_FICTION = "non-fiction"
    FICTION = "fiction"
    EDUCATIONAL = "educational"
    BUSINESS = "business"
    SELF_HELP = "self-help"
    CHILDREN = "children"
    BIOGRAPHY = "biography"
    HEALTH = "health"
    TECHNOLOGY = "technology"
    HISTORY = "history"

class WritingTone(str, Enum):
    PROFESSIONAL = "professional"
    CONVERSATIONAL = "conversational"
    ACADEMIC = "academic"
    FRIENDLY = "friendly"
    FORMAL = "formal"
    PERSUASIVE = "persuasive"

class ComplexityLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"

class WritingPerspective(str, Enum):
    FIRST_PERSON = "first-person"
    SECOND_PERSON = "second-person"
    THIRD_PERSON = "third-person"

class TargetAudience(str, Enum):
    GENERAL = "general"
    PROFESSIONALS = "professionals"
    STUDENTS = "students"
    CHILDREN = "children"
    SENIORS = "seniors"
    BEGINNERS = "beginners"
    ADVANCED_USERS = "advanced-users"

class LongFormBookRequest(BaseModel):
    """Enhanced request model based on your fantastic Longbookgeneration2.py BookSettings"""
    model_config = ConfigDict(protected_namespaces=())
    
    # Core book concept and settings
    concept: str = Field(..., description="What book do you want to write? Describe your concept")
    genre: BookGenre = Field(..., description="Book genre")
    target_audience: TargetAudience = Field(..., description="Target audience for the book")
    book_length: BookLength = Field(..., description="Desired book length")
    tone: WritingTone = Field(WritingTone.ACADEMIC, description="Writing tone/style")
    complexity: ComplexityLevel = Field(ComplexityLevel.INTERMEDIATE, description="Content complexity level")
    perspective: WritingPerspective = Field(WritingPerspective.THIRD_PERSON, description="Writing perspective")
    
    # Structure settings (enhanced from your BookSettings)
    chapters_count: int = Field(10, ge=5, le=20, description="Number of chapters (5-20)")
    sections_per_chapter: int = Field(6, ge=3, le=10, description="Sections per chapter (3-10)")
    pages_per_section: int = Field(3, ge=1, le=8, description="Pages per section (1-8)")
    
    # Features (enhanced from your include_* settings)
    include_toc: bool = Field(True, description="Include Table of Contents")
    include_images: bool = Field(True, description="Include relevant images with AI search")
    include_bibliography: bool = Field(True, description="Include Bibliography and sources")
    include_index: bool = Field(False, description="Include Index")
    include_cover: bool = Field(True, description="Include cover design information")
    
    # Metadata (from your BookSettings)
    author_name: str = Field("AI Generated", description="Author name")
    book_title: Optional[str] = Field(None, description="Book title (auto-generated if not provided)")

class BookChapter(BaseModel):
    """Enhanced chapter model with image support"""
    chapter_number: int
    title: str
    content: str
    sections: List[str]
    images: List[Dict[str, Any]] = []  # Enhanced with image data
    word_count: int = 0
    estimated_reading_time: Optional[int] = None  # Minutes

class BookMetadata(BaseModel):
    """Enhanced metadata based on your statistics"""
    title: str
    author: str
    genre: str
    target_audience: str
    total_chapters: int
    total_pages: int
    total_words: int
    total_images: int
    generation_time: float
    created_at: str
    estimated_reading_time: Optional[int] = None  # Minutes
    complexity_level: Optional[str] = None
    writing_perspective: Optional[str] = None

class BookImage(BaseModel):
    """Model for book images"""
    caption: str
    data: str  # Base64 encoded image
    source: Optional[str] = None
    chapter_number: Optional[int] = None
    size_bytes: Optional[int] = None

class LongFormBookResponse(BaseModel):
    """Enhanced response model"""
    book_metadata: BookMetadata
    table_of_contents: List[Dict[str, str]]
    chapters: List[BookChapter]
    bibliography: Optional[List[str]] = None
    cover_design_info: Optional[Dict[str, Any]] = None
    download_links: Dict[str, str] = {}
    generation_stats: Optional[Dict[str, Any]] = None

class StreamingBookResponse(BaseModel):
    """Enhanced streaming response for SSE"""
    type: str  # Event type for SSE
    message: Optional[str] = None
    progress: Optional[int] = None  # 0-100
    data: Optional[Dict[str, Any]] = None
    chapter_number: Optional[int] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: Optional[str] = None
    
    # Enhanced fields for better streaming
    book_title: Optional[str] = None
    chapters_count: Optional[int] = None
    include_images: Optional[bool] = None
    current_operation: Optional[str] = None

class BookGenerationSettings(BaseModel):
    """Settings model for frontend configuration"""
    genres: List[Dict[str, str]]
    target_audiences: List[Dict[str, str]]
    book_lengths: List[Dict[str, str]]
    writing_tones: List[Dict[str, str]]
    complexity_levels: List[str]
    writing_perspectives: List[str]
    structure_limits: Dict[str, Dict[str, int]]
    features: Dict[str, str]
    pricing: Dict[str, int]
    estimated_time: str
    sse_info: Dict[str, Any]

class BookUsageStats(BaseModel):
    """Statistics model for user's book history"""
    total_books: int
    completed_books: int
    total_words: int
    total_images: int
    total_credits_used: int
    average_generation_time: float
    most_used_genre: Optional[str] = None
    favorite_complexity: Optional[str] = None
