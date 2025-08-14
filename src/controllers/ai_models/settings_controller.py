from typing import Dict, Any, List, Optional
from src.config.mongodb import MongoDB
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AIModelSettingsController:
    @staticmethod
    def _prepare_document_data(doc: dict) -> dict:
        """Convert ObjectId to string"""
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])
        return doc

    async def get_model_settings(self, model_slug: str) -> Dict[str, Any]:
        """Get dynamic settings for a specific AI model"""
        try:
            settings_collection = await MongoDB.get_collection("ai_model_settings")
            settings = await settings_collection.find_one({
                "model_slug": model_slug,
                "is_active": True
            })
            
            if not settings:
                raise ValueError(f"Settings not found for model: {model_slug}")
            
            settings = self._prepare_document_data(settings)
            
            return {
                "model_slug": settings["model_slug"],
                "model_name": settings["model_name"],
                "version": settings["version"],
                "settings_schema": settings["settings_schema"],
                "ui_layout": settings["ui_layout"],
                "pricing": settings["pricing"],
                "estimated_time": settings["estimated_time"]
            }
            
        except Exception as e:
            logger.error(f"Error getting model settings: {str(e)}")
            raise e

    async def get_all_model_settings(self) -> Dict[str, Any]:
        """Get settings for all active AI models"""
        try:
            settings_collection = await MongoDB.get_collection("ai_model_settings")
            cursor = settings_collection.find({"is_active": True})
            
            models_settings = {}
            async for settings in cursor:
                settings = self._prepare_document_data(settings)
                models_settings[settings["model_slug"]] = {
                    "model_name": settings["model_name"],
                    "version": settings["version"],
                    "settings_schema": settings["settings_schema"],
                    "ui_layout": settings["ui_layout"],
                    "pricing": settings["pricing"],
                    "estimated_time": settings["estimated_time"]
                }
            
            return models_settings
            
        except Exception as e:
            logger.error(f"Error getting all model settings: {str(e)}")
            raise e

    async def update_model_settings(
        self, 
        model_slug: str, 
        settings_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update settings for a specific AI model"""
        try:
            settings_collection = await MongoDB.get_collection("ai_model_settings")
            
            # Check if settings exist
            existing = await settings_collection.find_one({"model_slug": model_slug})
            if not existing:
                raise ValueError(f"Settings not found for model: {model_slug}")
            
            # Update settings
            update_data = {
                **settings_data,
                "updated_at": datetime.utcnow()
            }
            
            await settings_collection.update_one(
                {"model_slug": model_slug},
                {"$set": update_data}
            )
            
            # Return updated settings
            return await self.get_model_settings(model_slug)
            
        except Exception as e:
            logger.error(f"Error updating model settings: {str(e)}")
            raise e

    async def validate_user_input(
        self, 
        model_slug: str, 
        user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate user input against model settings schema"""
        try:
            settings = await self.get_model_settings(model_slug)
            schema = settings["settings_schema"]
            
            validated_data = {}
            errors = []
            
            # Flatten schema for easier validation
            flattened_schema = self._flatten_schema(schema)
            
            for field_path, field_config in flattened_schema.items():
                value = self._get_nested_value(user_input, field_path)
                
                # Check required fields
                if field_config.get("required", False) and value is None:
                    errors.append(f"Field '{field_path}' is required")
                    continue
                
                # Validate field type and constraints
                if value is not None:
                    validation_result = self._validate_field(field_path, value, field_config)
                    if validation_result["valid"]:
                        self._set_nested_value(validated_data, field_path, value)
                    else:
                        errors.extend(validation_result["errors"])
                else:
                    # Set default value if provided
                    if "default" in field_config:
                        self._set_nested_value(validated_data, field_path, field_config["default"])
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "validated_data": validated_data
            }
            
        except Exception as e:
            logger.error(f"Error validating user input: {str(e)}")
            raise e

    def _flatten_schema(self, schema: Dict[str, Any], prefix: str = "") -> Dict[str, Any]:
        """Flatten nested schema structure"""
        flattened = {}
        
        for key, value in schema.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) and "type" in value:
                # This is a field definition
                flattened[current_path] = value
            elif isinstance(value, dict):
                # This is a nested group, recurse
                flattened.update(self._flatten_schema(value, current_path))
        
        return flattened

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """Set value in nested dictionary using dot notation"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value

    def _validate_field(self, field_path: str, value: Any, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual field based on its configuration"""
        errors = []
        
        field_type = config.get("type", "text")
        
        # Type-specific validation
        if field_type == "range":
            if not isinstance(value, (int, float)):
                errors.append(f"Field '{field_path}' must be a number")
            else:
                min_val = config.get("min")
                max_val = config.get("max")
                if min_val is not None and value < min_val:
                    errors.append(f"Field '{field_path}' must be at least {min_val}")
                if max_val is not None and value > max_val:
                    errors.append(f"Field '{field_path}' must be at most {max_val}")
        
        elif field_type == "select":
            valid_options = [opt["value"] for opt in config.get("options", [])]
            if value not in valid_options:
                errors.append(f"Field '{field_path}' must be one of: {', '.join(valid_options)}")
        
        elif field_type in ["text", "textarea"]:
            if not isinstance(value, str):
                errors.append(f"Field '{field_path}' must be a string")
            else:
                validation = config.get("validation", {})
                min_length = validation.get("min_length")
                max_length = validation.get("max_length")
                
                if min_length and len(value) < min_length:
                    errors.append(f"Field '{field_path}' must be at least {min_length} characters")
                if max_length and len(value) > max_length:
                    errors.append(f"Field '{field_path}' must be at most {max_length} characters")
        
        elif field_type == "checkbox":
            if not isinstance(value, bool):
                errors.append(f"Field '{field_path}' must be true or false")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors
        }
