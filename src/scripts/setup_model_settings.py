import asyncio
import sys
import os
from datetime import datetime
from typing import Dict, Any

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config.mongodb import MongoDB

class ModelSettingsSetup:
    """Class to handle AI model settings setup"""
    
    def __init__(self):
        self.settings_collection = None
    
    async def initialize(self):
        """Initialize MongoDB connection"""
        await MongoDB.connect()
        self.settings_collection = await MongoDB.get_collection("ai_model_settings")
        print("✅ Connected to MongoDB successfully")
    
    async def setup_long_form_book_settings(self):
        """Setup settings for long-form book model"""
        print("🚀 Setting up Long-form Book model settings...")
        
        settings_data = {
            "model_slug": "long-form-book",
            "model_name": "Long-form Book",
            "version": "1.0",
            "settings_schema": {
                "basic_info": {
                    "concept": {
                        "type": "textarea",
                        "label": "Book Concept",
                        "description": "What book do you want to write? Describe your concept",
                        "required": True,
                        "placeholder": "e.g., Complete understanding handbook of Indian Agriculture Overview",
                        "validation": {
                            "min_length": 10,
                            "max_length": 500
                        }
                    },
                    "book_title": {
                        "type": "text",
                        "label": "Book Title",
                        "description": "Book title (auto-generated if not provided)",
                        "required": False,
                        "placeholder": "Leave blank for auto-generation"
                    },
                    "author_name": {
                        "type": "text",
                        "label": "Author Name",
                        "description": "Author name for the book",
                        "required": False,
                        "default": "AI Generated"
                    }
                },
                "book_properties": {
                    "genre": {
                        "type": "select",
                        "label": "Book Genre",
                        "description": "Select the book genre",
                        "required": True,
                        "options": [
                            {"value": "non-fiction", "label": "Non-Fiction"},
                            {"value": "fiction", "label": "Fiction"},
                            {"value": "educational", "label": "Educational"},
                            {"value": "business", "label": "Business"},
                            {"value": "self-help", "label": "Self Help"},
                            {"value": "children", "label": "Children"},
                            {"value": "biography", "label": "Biography"},
                            {"value": "health", "label": "Health"},
                            {"value": "technology", "label": "Technology"},
                            {"value": "history", "label": "History"}
                        ]
                    },
                    "target_audience": {
                        "type": "select",
                        "label": "Target Audience",
                        "description": "Who is this book for?",
                        "required": True,
                        "options": [
                            {"value": "general", "label": "General Public"},
                            {"value": "professionals", "label": "Professionals"},
                            {"value": "students", "label": "Students"},
                            {"value": "children", "label": "Children"},
                            {"value": "seniors", "label": "Seniors"},
                            {"value": "beginners", "label": "Beginners"},
                            {"value": "advanced-users", "label": "Advanced Users"}
                        ]
                    },
                    "book_length": {
                        "type": "select",
                        "label": "Book Length",
                        "description": "Desired book length",
                        "required": True,
                        "default": "standard",
                        "options": [
                            {"value": "short", "label": "Short (50-100 pages)"},
                            {"value": "standard", "label": "Standard (150-250 pages)"},
                            {"value": "extended", "label": "Extended (300-400 pages)"},
                            {"value": "epic", "label": "Epic (500+ pages)"}
                        ]
                    }
                },
                "writing_style": {
                    "tone": {
                        "type": "select",
                        "label": "Writing Tone",
                        "description": "Choose the writing style",
                        "required": True,
                        "default": "academic",
                        "options": [
                            {"value": "professional", "label": "Professional"},
                            {"value": "conversational", "label": "Conversational"},
                            {"value": "academic", "label": "Academic"},
                            {"value": "friendly", "label": "Friendly"},
                            {"value": "formal", "label": "Formal"},
                            {"value": "persuasive", "label": "Persuasive"}
                        ]
                    },
                    "complexity": {
                        "type": "select",
                        "label": "Complexity Level",
                        "description": "Content complexity level",
                        "required": True,
                        "default": "intermediate",
                        "options": [
                            {"value": "beginner", "label": "Beginner"},
                            {"value": "intermediate", "label": "Intermediate"},
                            {"value": "advanced", "label": "Advanced"}
                        ]
                    },
                    "perspective": {
                        "type": "select",
                        "label": "Writing Perspective",
                        "description": "Narrative perspective",
                        "required": True,
                        "default": "third-person",
                        "options": [
                            {"value": "first-person", "label": "First Person"},
                            {"value": "second-person", "label": "Second Person"},
                            {"value": "third-person", "label": "Third Person"}
                        ]
                    }
                },
                "structure": {
                    "chapters_count": {
                        "type": "range",
                        "label": "Number of Chapters",
                        "description": "How many chapters do you want?",
                        "required": True,
                        "default": 10,
                        "min": 5,
                        "max": 20,
                        "step": 1
                    },
                    "sections_per_chapter": {
                        "type": "range",
                        "label": "Sections per Chapter",
                        "description": "How many sections in each chapter?",
                        "required": True,
                        "default": 6,
                        "min": 3,
                        "max": 10,
                        "step": 1
                    },
                    "pages_per_section": {
                        "type": "range",
                        "label": "Pages per Section",
                        "description": "Approximately how many pages per section?",
                        "required": True,
                        "default": 3,
                        "min": 1,
                        "max": 8,
                        "step": 1
                    }
                },
                "features": {
                    "include_toc": {
                        "type": "checkbox",
                        "label": "Include Table of Contents",
                        "description": "Add a comprehensive table of contents",
                        "default": True
                    },
                    "include_images": {
                        "type": "checkbox",
                        "label": "Include Images",
                        "description": "Add relevant images throughout the book",
                        "default": True
                    },
                    "include_bibliography": {
                        "type": "checkbox",
                        "label": "Include Bibliography",
                        "description": "Add bibliography and references",
                        "default": True
                    },
                    "include_index": {
                        "type": "checkbox",
                        "label": "Include Index",
                        "description": "Add an index at the end",
                        "default": False
                    },
                    "include_cover": {
                        "type": "checkbox",
                        "label": "Include Cover Design",
                        "description": "Generate cover design information",
                        "default": True
                    }
                }
            },
            "ui_layout": {
                "sections": [
                    {
                        "title": "Basic Information",
                        "fields": ["basic_info.concept", "basic_info.book_title", "basic_info.author_name"],
                        "collapsible": False
                    },
                    {
                        "title": "Book Properties", 
                        "fields": ["book_properties.genre", "book_properties.target_audience", "book_properties.book_length"],
                        "collapsible": False
                    },
                    {
                        "title": "Writing Style",
                        "fields": ["writing_style.tone", "writing_style.complexity", "writing_style.perspective"],
                        "collapsible": True
                    },
                    {
                        "title": "Book Structure",
                        "fields": ["structure.chapters_count", "structure.sections_per_chapter", "structure.pages_per_section"],
                        "collapsible": True
                    },
                    {
                        "title": "Additional Features",
                        "fields": ["features.include_toc", "features.include_images", "features.include_bibliography", "features.include_index", "features.include_cover"],
                        "collapsible": True
                    }
                ]
            },
            "pricing": {
                "credits_per_use": 50,
                "premium_credits": 75
            },
            "estimated_time": "15-30 minutes",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Upsert the settings
        result = await self.settings_collection.update_one(
            {"model_slug": "long-form-book"},
            {"$set": settings_data},
            upsert=True
        )
        
        if result.upserted_id:
            print("✅ Long-form Book settings created successfully!")
        else:
            print("✅ Long-form Book settings updated successfully!")
        
        return True
    
    async def setup_audio_translation_settings(self):
        """Setup settings for audio translation model"""
        print("🚀 Setting up Audio Translation model settings...")
        
        settings_data = {
            "model_slug": "audio-translation",
            "model_name": "Audio Translation",
            "version": "1.0",
            "settings_schema": {
                "audio_input": {
                    "audio_file": {
                        "type": "file",
                        "label": "Audio File",
                        "description": "Upload your audio file for translation",
                        "required": True,
                        "accept": ["audio/mp3", "audio/wav", "audio/m4a"],
                        "max_size": "50MB"
                    }
                },
                "translation_settings": {
                    "target_language": {
                        "type": "select",
                        "label": "Target Language",
                        "description": "Language to translate to",
                        "required": True,
                        "options": [
                            {"value": "en", "label": "English"},
                            {"value": "es", "label": "Spanish"},
                            {"value": "fr", "label": "French"},
                            {"value": "de", "label": "German"},
                            {"value": "it", "label": "Italian"},
                            {"value": "pt", "label": "Portuguese"},
                            {"value": "ru", "label": "Russian"},
                            {"value": "ja", "label": "Japanese"},
                            {"value": "ko", "label": "Korean"},
                            {"value": "zh", "label": "Chinese"},
                            {"value": "ar", "label": "Arabic"},
                            {"value": "hi", "label": "Hindi"},
                            {"value": "bn", "label": "Bengali"},
                            {"value": "ta", "label": "Tamil"},
                            {"value": "te", "label": "Telugu"},
                            {"value": "mr", "label": "Marathi"}
                        ]
                    },
                    "preserve_voice": {
                        "type": "checkbox",
                        "label": "Preserve Original Voice",
                        "description": "Maintain the original speaker's voice characteristics",
                        "default": True
                    },
                    "preserve_emotion": {
                        "type": "checkbox",
                        "label": "Preserve Emotion",
                        "description": "Keep the emotional tone of the original audio",
                        "default": True
                    }
                },
                "output_settings": {
                    "output_format": {
                        "type": "select",
                        "label": "Output Format",
                        "description": "Choose the output audio format",
                        "required": True,
                        "default": "mp3",
                        "options": [
                            {"value": "mp3", "label": "MP3"},
                            {"value": "wav", "label": "WAV"}
                        ]
                    },
                    "quality": {
                        "type": "select",
                        "label": "Audio Quality",
                        "description": "Select output quality",
                        "required": True,
                        "default": "high",
                        "options": [
                            {"value": "standard", "label": "Standard"},
                            {"value": "high", "label": "High"},
                            {"value": "premium", "label": "Premium"}
                        ]
                    }
                }
            },
            "ui_layout": {
                "sections": [
                    {
                        "title": "Audio Input",
                        "fields": ["audio_input.audio_file"],
                        "collapsible": False
                    },
                    {
                        "title": "Translation Settings",
                        "fields": ["translation_settings.target_language", "translation_settings.preserve_voice", "translation_settings.preserve_emotion"],
                        "collapsible": False
                    },
                    {
                        "title": "Output Settings",
                        "fields": ["output_settings.output_format", "output_settings.quality"],
                        "collapsible": True
                    }
                ]
            },
            "pricing": {
                "credits_per_use": 10,
                "premium_credits": 15
            },
            "estimated_time": "2-5 minutes",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Upsert the settings
        result = await self.settings_collection.update_one(
            {"model_slug": "audio-translation"},
            {"$set": settings_data},
            upsert=True
        )
        
        if result.upserted_id:
            print("✅ Audio Translation settings created successfully!")
        else:
            print("✅ Audio Translation settings updated successfully!")
        
        return True
    
    async def setup_voice_cloning_settings(self):
        """Setup settings for voice cloning model"""
        print("🚀 Setting up Voice Cloning model settings...")
        
        settings_data = {
            "model_slug": "voice-cloning",
            "model_name": "Voice Cloning",
            "version": "1.0",
            "settings_schema": {
                "voice_input": {
                    "reference_audio": {
                        "type": "file",
                        "label": "Reference Audio",
                        "description": "Upload a clear audio sample of the voice to clone (minimum 30 seconds)",
                        "required": True,
                        "accept": ["audio/mp3", "audio/wav", "audio/m4a"],
                        "max_size": "100MB"
                    },
                    "text_content": {
                        "type": "textarea",
                        "label": "Text to Speak",
                        "description": "Enter the text you want the cloned voice to speak",
                        "required": True,
                        "validation": {
                            "min_length": 10,
                            "max_length": 5000
                        }
                    }
                },
                "voice_settings": {
                    "language": {
                        "type": "select",
                        "label": "Voice Language",
                        "description": "Language of the voice",
                        "required": True,
                        "options": [
                            {"value": "en-US", "label": "English (US)"},
                            {"value": "en-GB", "label": "English (UK)"},
                            {"value": "es-ES", "label": "Spanish"},
                            {"value": "fr-FR", "label": "French"},
                            {"value": "de-DE", "label": "German"},
                            {"value": "it-IT", "label": "Italian"},
                            {"value": "pt-BR", "label": "Portuguese"},
                            {"value": "hi-IN", "label": "Hindi"},
                            {"value": "ja-JP", "label": "Japanese"},
                            {"value": "ko-KR", "label": "Korean"}
                        ]
                    },
                    "tone": {
                        "type": "select",
                        "label": "Voice Tone",
                        "description": "Emotional tone for the speech",
                        "required": True,
                        "default": "neutral",
                        "options": [
                            {"value": "neutral", "label": "Neutral"},
                            {"value": "professional", "label": "Professional"},
                            {"value": "friendly", "label": "Friendly"},
                            {"value": "excited", "label": "Excited"},
                            {"value": "calm", "label": "Calm"},
                            {"value": "authoritative", "label": "Authoritative"}
                        ]
                    },
                    "speed": {
                        "type": "range",
                        "label": "Speaking Speed",
                        "description": "Adjust the speaking speed",
                        "required": True,
                        "default": 1.0,
                        "min": 0.5,
                        "max": 2.0,
                        "step": 0.1
                    },
                    "pitch": {
                        "type": "range",
                        "label": "Voice Pitch",
                        "description": "Adjust the voice pitch",
                        "required": True,
                        "default": 1.0,
                        "min": 0.5,
                        "max": 1.5,
                        "step": 0.1
                    }
                },
                "quality_settings": {
                    "similarity_boost": {
                        "type": "checkbox",
                        "label": "Similarity Boost",
                        "description": "Enhance voice similarity to original",
                        "default": True
                    },
                    "stability": {
                        "type": "range",
                        "label": "Voice Stability",
                        "description": "Control voice consistency",
                        "required": True,
                        "default": 0.75,
                        "min": 0.0,
                        "max": 1.0,
                        "step": 0.05
                    }
                }
            },
            "ui_layout": {
                "sections": [
                    {
                        "title": "Voice Input",
                        "fields": ["voice_input.reference_audio", "voice_input.text_content"],
                        "collapsible": False
                    },
                    {
                        "title": "Voice Settings",
                        "fields": ["voice_settings.language", "voice_settings.tone", "voice_settings.speed", "voice_settings.pitch"],
                        "collapsible": False
                    },
                    {
                        "title": "Quality Settings",
                        "fields": ["quality_settings.similarity_boost", "quality_settings.stability"],
                        "collapsible": True
                    }
                ]
            },
            "pricing": {
                "credits_per_use": 25,
                "premium_credits": 35
            },
            "estimated_time": "5-10 minutes",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "is_active": True
        }
        
        # Upsert the settings
        result = await self.settings_collection.update_one(
            {"model_slug": "voice-cloning"},
            {"$set": settings_data},
            upsert=True
        )
        
        if result.upserted_id:
            print("✅ Voice Cloning settings created successfully!")
        else:
            print("✅ Voice Cloning settings updated successfully!")
        
        return True
    
    async def list_all_settings(self):
        """List all configured model settings"""
        print("\n📋 Current Model Settings:")
        print("=" * 50)
        
        cursor = self.settings_collection.find({"is_active": True})
        count = 0
        
        async for settings in cursor:
            count += 1
            print(f"{count}. {settings['model_name']} ({settings['model_slug']})")
            print(f"   Version: {settings['version']}")
            print(f"   Credits: {settings['pricing']['credits_per_use']}")
            print(f"   Estimated Time: {settings['estimated_time']}")
            print(f"   Last Updated: {settings['updated_at'].strftime('%Y-%m-%d %H:%M:%S')}")
            print("-" * 30)
        
        if count == 0:
            print("No active model settings found.")
        else:
            print(f"Total: {count} active model(s)")
    
    async def cleanup(self):
        """Close MongoDB connection"""
        await MongoDB.close()
        print("🔌 MongoDB connection closed")

# Main setup functions
async def setup_all_models():
    """Setup all AI model settings"""
    setup = ModelSettingsSetup()
    
    try:
        await setup.initialize()
        
        # Setup all models
        await setup.setup_long_form_book_settings()
        await setup.setup_audio_translation_settings()
        await setup.setup_voice_cloning_settings()
        
        # List all settings
        await setup.list_all_settings()
        
        print("\n🎉 All model settings configured successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up model settings: {e}")
        raise
    finally:
        await setup.cleanup()

async def setup_single_model(model_slug: str):
    """Setup settings for a single model"""
    setup = ModelSettingsSetup()
    
    try:
        await setup.initialize()
        
        if model_slug == "long-form-book":
            await setup.setup_long_form_book_settings()
        elif model_slug == "audio-translation":
            await setup.setup_audio_translation_settings()
        elif model_slug == "voice-cloning":
            await setup.setup_voice_cloning_settings()
        else:
            print(f"❌ Unknown model slug: {model_slug}")
            return
        
        print(f"🎉 {model_slug} settings configured successfully!")
        
    except Exception as e:
        print(f"❌ Error setting up {model_slug} settings: {e}")
        raise
    finally:
        await setup.cleanup()

async def list_models():
    """List all configured models"""
    setup = ModelSettingsSetup()
    
    try:
        await setup.initialize()
        await setup.list_all_settings()
    except Exception as e:
        print(f"❌ Error listing models: {e}")
        raise
    finally:
        await setup.cleanup()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Setup AI Model Settings")
    parser.add_argument(
        "action", 
        choices=["all", "long-form-book", "audio-translation", "voice-cloning", "list"],
        help="Action to perform"
    )
    
    args = parser.parse_args()
    
    print("🚀 AI Model Settings Setup")
    print("=" * 30)
    
    if args.action == "all":
        asyncio.run(setup_all_models())
    elif args.action == "list":
        asyncio.run(list_models())
    else:
        asyncio.run(setup_single_model(args.action))
