from typing import Dict, List
from src.models.ai_models.base_ai_model import AIModelCategory

AI_MODELS_CONFIG = {
    # AUDIO PROCESSING MODELS
    "audio-translation": {
        "name": "Audio Translation",
        "category": AIModelCategory.AUDIO,
        "description": "Multilingual voice conversion",
        "success_rate": 97,
        "features": ["Multilingual", "Voice Preservation", "Real-time"],
        "input_types": ["audio/mp3", "audio/wav", "audio/m4a"],
        "output_types": ["audio/mp3", "audio/wav"],
        "pricing": {"credits_per_use": 10, "premium_credits": 15},
        "estimated_time": "2-5 minutes",
        "tags": ["Popular", "97% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Translate audio into 20+ languages while preserving the original voice's emotion, tone, and speaking style for authentic cross-language communication.",
            "display_name": "Audio Translation",
            "labels": ["Audio Translation", "Multilingual"]
        }
    },
    
    "voice-cloning": {
        "name": "Voice Cloning",
        "category": AIModelCategory.AUDIO,
        "description": "AI-powered voice replication",
        "success_rate": 94,
        "features": ["AI Voice", "Voice Replication"],
        "input_types": ["audio/mp3", "audio/wav"],
        "output_types": ["audio/mp3", "audio/wav"],
        "pricing": {"credits_per_use": 15, "premium_credits": 20},
        "estimated_time": "5-10 minutes",
        "tags": ["AI Powered", "94% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Create an accurate digital clone of any voice from just a few audio samples. Perfect for content creation, personalization, and accessibility.",
            "display_name": "Voice Cloning",
            "labels": ["Voice Cloning", "AI Voice"]
        }
    },
    
    "audio-enhancement": {
        "name": "Audio Enhancement",
        "category": AIModelCategory.AUDIO,
        "description": "Professional audio cleanup",
        "success_rate": 92,
        "features": ["Noise Reduction", "Echo Removal", "Clarity Enhancement"],
        "input_types": ["audio/mp3", "audio/wav", "audio/m4a"],
        "output_types": ["audio/mp3", "audio/wav"],
        "pricing": {"credits_per_use": 12, "premium_credits": 18},
        "estimated_time": "3-8 minutes",
        "tags": ["Pro Tools", "92% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Transform low-quality audio into crystal-clear recordings with advanced noise reduction, echo removal, and clarity enhancement algorithms.",
            "display_name": "Audio Enhancement",
            "labels": ["Audio Enhancement", "Noise Reduction"]
        }
    },

    # TEXT PROCESSING MODELS
    "text-to-speech": {
        "name": "Text to Speech",
        "category": AIModelCategory.AUDIO,
        "description": "Natural voice synthesis",
        "success_rate": 94,
        "features": ["Voice Synthesis", "Multilingual", "Customizable Voices"],
        "input_types": ["text/plain"],
        "output_types": ["audio/mp3", "audio/wav"],
        "pricing": {"credits_per_use": 5, "premium_credits": 8},
        "estimated_time": "1-2 minutes",
        "tags": ["Popular", "94% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Convert text into natural-sounding speech with customizable voices and multilingual support.",
            "display_name": "Convert texts to voice",
            "labels": ["Text-to-Speech", "Voice Synthesis"]
        }
    },
    
    "summarization": {
        "name": "Text Summarization",
        "category": AIModelCategory.TEXT,
        "description": "Intelligent text summarization",
        "success_rate": 97,
        "features": ["Text Analysis", "NLP", "Concise Summaries"],
        "input_types": ["text/plain", "application/pdf"],
        "output_types": ["text/plain"],
        "pricing": {"credits_per_use": 3, "premium_credits": 5},
        "estimated_time": "30 seconds",
        "tags": ["AI Powered", "97% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Create concise, meaningful summaries of large text documents using advanced NLP technology.",
            "display_name": "Summarize",
            "labels": ["Summarization", "Text Analysis"]
        }
    },

    # DATA PROCESSING MODELS
    "excel-to-charts": {
        "name": "Excel to Charts",
        "category": AIModelCategory.IMAGE,
        "description": "Visualize spreadsheet data",
        "success_rate": 92,
        "features": ["Data Visualization", "Excel Processing", "CSV Support"],
        "input_types": ["application/vnd.ms-excel", "text/csv", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"],
        "output_types": ["image/png", "image/svg+xml", "audio/mp3"],
        "pricing": {"credits_per_use": 8, "premium_credits": 12},
        "estimated_time": "2-5 minutes",
        "tags": ["Data Viz", "92% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Transform Excel or CSV data into comprehensive audio summaries and visual charts.",
            "display_name": "Excel to Charts",
            "labels": ["Excel", "CSV"]
        }
    },

    # CAREER ENHANCEMENT MODELS
    "ats-score": {
        "name": "ATS Score",
        "category": AIModelCategory.TEXT,
        "description": "Resume optimization scoring",
        "success_rate": 96,
        "features": ["ATS Compatibility", "Resume Analysis", "Improvement Suggestions"],
        "input_types": ["application/pdf", "text/plain", "application/msword"],
        "output_types": ["application/json", "text/plain"],
        "pricing": {"credits_per_use": 6, "premium_credits": 10},
        "estimated_time": "1-2 minutes",
        "tags": ["Career Boost", "96% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Evaluate resumes against job descriptions for ATS compatibility and provide detailed improvement suggestions.",
            "display_name": "ATS Score",
            "labels": ["ATS", "Resume Analysis"]
        }
    },
    
    "resume-analyzer": {
        "name": "Resume Analyzer",
        "category": AIModelCategory.TEXT,
        "description": "Professional resume enhancement",
        "success_rate": 94,
        "features": ["Resume Enhancement", "Industry Recommendations", "Best Practices"],
        "input_types": ["application/pdf", "text/plain", "application/msword"],
        "output_types": ["text/plain", "application/json"],
        "pricing": {"credits_per_use": 8, "premium_credits": 12},
        "estimated_time": "2-4 minutes",
        "tags": ["Pro Tools", "94% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Get tailored suggestions to improve your resume with industry-specific recommendations and best practices.",
            "display_name": "Resume Analyser",
            "labels": ["Resume Enhancement", "Career"]
        }
    },

    # CONTENT GENERATION MODELS
    "long-form-book": {
        "name": "Long-form Book",
        "category": AIModelCategory.CONTENT,
        "description": "Generate comprehensive books",
        "success_rate": 93,
        "features": ["Chapter Structure", "Cover Design", "Image Integration", "Research References"],
        "input_types": ["text/plain"],
        "output_types": ["application/pdf", "text/plain", "image/png"],
        "pricing": {"credits_per_use": 50, "premium_credits": 75},
        "estimated_time": "15-30 minutes",
        "tags": ["Content Generation", "93% Success", "Start Creating"],
        "extra_info": {
            "description_detail": "Generate comprehensive books with chapters, cover page, images, and research references",
            "display_name": "Long-form Book",
            "labels": ["Chapter Structure", "Cover Design", "Image Integration", "+2 more"]
        }
    },
    
    "research-paper": {
        "name": "Research Paper",
        "category": AIModelCategory.CONTENT,
        "description": "Create academic papers",
        "success_rate": 91,
        "features": ["Abstract", "Literature Review", "Methodology", "Citations"],
        "input_types": ["text/plain"],
        "output_types": ["application/pdf", "text/plain"],
        "pricing": {"credits_per_use": 40, "premium_credits": 60},
        "estimated_time": "10-20 minutes",
        "tags": ["Academic", "91% Success", "Start Creating"],
        "extra_info": {
            "description_detail": "Create academic papers with abstract, methodology, results, citations, and appendix",
            "display_name": "Research Paper",
            "labels": ["Abstract", "Literature Review", "Methodology", "+2 more"]
        }
    },
    
    "course-material": {
        "name": "Course Material",
        "category": AIModelCategory.CONTENT,
        "description": "Develop comprehensive courses",
        "success_rate": 89,
        "features": ["Lesson Modules", "Interactive Exercises", "Diagrams", "Assignments"],
        "input_types": ["text/plain"],
        "output_types": ["application/pdf", "text/plain", "image/png"],
        "pricing": {"credits_per_use": 60, "premium_credits": 90},
        "estimated_time": "20-40 minutes",
        "tags": ["Educational", "89% Success", "Start Creating"],
        "extra_info": {
            "description_detail": "Develop comprehensive courses with lesson modules, diagrams, and assignments",
            "display_name": "Course Material",
            "labels": ["Lesson Modules", "Interactive Exercises", "Diagrams", "+2 more"]
        }
    },
    
    "professional-letter": {
        "name": "Professional Letter",
        "category": AIModelCategory.CONTENT,
        "description": "Craft formal and informal letters",
        "success_rate": 96,
        "features": ["Letterhead", "Formal Structure", "Custom Branding", "Professional Formatting"],
        "input_types": ["text/plain"],
        "output_types": ["application/pdf", "text/plain"],
        "pricing": {"credits_per_use": 5, "premium_credits": 8},
        "estimated_time": "2-5 minutes",
        "tags": ["Business", "96% Success", "Start Creating"],
        "extra_info": {
            "description_detail": "Craft formal and informal letters with custom branding and formatting",
            "display_name": "Professional Letter",
            "labels": ["Letterhead", "Formal Structure", "Custom Branding", "+2 more"]
        }
    },

    # VIDEO PROCESSING MODELS
    "ai-video-creator": {
        "name": "AI Video Creator",
        "category": AIModelCategory.VIDEO,
        "description": "Create cinematic videos from text",
        "success_rate": 95,
        "features": ["Video Generation", "AI Animation", "Cinematic Quality"],
        "input_types": ["text/plain"],
        "output_types": ["video/mp4"],
        "pricing": {"credits_per_use": 25, "premium_credits": 35},
        "estimated_time": "10-15 minutes",
        "tags": ["AI Powered", "95% Success", "Try Now"],
        "extra_info": {
            "description_detail": "Generate stunning animated videos from simple text descriptions using state-of-the-art AI technology. Perfect for content creators, marketers, and storytellers.",
            "display_name": "AI Video Creator",
            "labels": ["Video Generation", "AI Animation"]
        }
    }
}

def get_model_config(slug: str) -> Dict:
    return AI_MODELS_CONFIG.get(slug, {})

def get_all_models() -> List[Dict]:
    return list(AI_MODELS_CONFIG.values())

def get_models_by_category(category: AIModelCategory) -> List[Dict]:
    return [model for model in AI_MODELS_CONFIG.values() if model["category"] == category]

def get_popular_models() -> List[Dict]:
    return [model for model in AI_MODELS_CONFIG.values() if "Popular" in model.get("tags", [])]

def get_models_by_tag(tag: str) -> List[Dict]:
    return [model for model in AI_MODELS_CONFIG.values() if tag in model.get("tags", [])]
