"""
Model configuration management.
"""

import json
import os
import uuid
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config


def init_models_config():
    """Initialize models configuration file with default models."""
    if not os.path.exists(config.MODELS_CONFIG_PATH):
        default_models = [
            {
                "id": str(uuid.uuid4()),
                "name": "GPT-4o",
                "provider": "openai",
                "model_id": "gpt-4o",
                "api_url": "https://api.openai.com/v1",
                "api_key": "",
                "enabled": True,
                "is_default": True,
                "is_reasoning": False
            },
            {
                "id": str(uuid.uuid4()),
                "name": "GPT-4o-mini",
                "provider": "openai",
                "model_id": "gpt-4o-mini",
                "api_url": "https://api.openai.com/v1",
                "api_key": "",
                "enabled": True,
                "is_default": False,
                "is_reasoning": False
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Claude-3.5-Sonnet",
                "provider": "anthropic",
                "model_id": "claude-3-5-sonnet-20241022",
                "api_url": "https://api.anthropic.com",
                "api_key": "",
                "enabled": False,
                "is_default": False,
                "is_reasoning": False
            }
        ]
        save_models_config(default_models)


def load_models_config() -> list:
    """Load models configuration from file."""
    if not os.path.exists(config.MODELS_CONFIG_PATH):
        init_models_config()
    
    with open(config.MODELS_CONFIG_PATH, 'r') as f:
        return json.load(f)


def save_models_config(models: list):
    """Save models configuration to file."""
    with open(config.MODELS_CONFIG_PATH, 'w') as f:
        json.dump(models, f, indent=2)


def get_all_models() -> list:
    """Get all models configuration."""
    return load_models_config()


def get_enabled_models() -> list:
    """Get only enabled models (for user selection)."""
    models = load_models_config()
    return [m for m in models if m.get('enabled', False)]


def get_model_by_id(model_id: str) -> dict:
    """Get a specific model by ID."""
    models = load_models_config()
    for model in models:
        if model['id'] == model_id:
            return model
    return None


def get_default_model() -> dict:
    """Get the default model."""
    models = load_models_config()
    for model in models:
        if model.get('is_default', False) and model.get('enabled', False):
            return model
    # Return first enabled model if no default
    enabled = [m for m in models if m.get('enabled', False)]
    return enabled[0] if enabled else None


def ensure_default_model(models: list) -> list:
    """Ensure there is exactly one default model among enabled models when possible."""
    enabled_models = [m for m in models if m.get('enabled', False)]

    if not enabled_models:
        for model in models:
            model['is_default'] = False
        return models

    default_enabled_models = [m for m in enabled_models if m.get('is_default', False)]

    if not default_enabled_models:
        enabled_models[0]['is_default'] = True
        default_enabled_models = [enabled_models[0]]

    chosen_default_id = default_enabled_models[0]['id']

    for model in models:
        model['is_default'] = model['id'] == chosen_default_id

    return models


def add_model(model_data: dict) -> dict:
    """Add a new model configuration."""
    models = load_models_config()

    make_default = model_data.get('is_default', False) and model_data.get('enabled', False)

    if make_default:
        for model in models:
            model['is_default'] = False

    new_model = {
        "id": str(uuid.uuid4()),
        "name": model_data.get('name', 'New Model'),
        "provider": model_data.get('provider', 'openai'),
        "model_id": model_data.get('model_id', ''),
        "api_url": model_data.get('api_url', ''),
        "api_key": model_data.get('api_key', ''),
        "enabled": model_data.get('enabled', False),
        "is_default": make_default,
        "is_reasoning": model_data.get('is_reasoning', False)
    }

    models.append(new_model)
    models = ensure_default_model(models)
    save_models_config(models)

    return next((m for m in models if m['id'] == new_model['id']), new_model)


def update_model(model_id: str, model_data: dict) -> dict:
    """Update a model configuration."""
    models = load_models_config()
    
    for i, model in enumerate(models):
        if model['id'] == model_id:
            # If setting as default, unset other defaults first
            if model_data.get('is_default', False) and model_data.get('enabled', model['enabled']):
                for m in models:
                    m['is_default'] = False
            
            models[i].update({
                "name": model_data.get('name', model['name']),
                "provider": model_data.get('provider', model['provider']),
                "model_id": model_data.get('model_id', model['model_id']),
                "api_url": model_data.get('api_url', model['api_url']),
                "api_key": model_data.get('api_key', model['api_key']),
                "enabled": model_data.get('enabled', model['enabled']),
                "is_default": model_data.get('is_default', model['is_default']) and model_data.get('enabled', model['enabled']),
                "is_reasoning": model_data.get('is_reasoning', model.get('is_reasoning', False))
            })

            models = ensure_default_model(models)
            save_models_config(models)
            return models[i]
    
    return None


def delete_model(model_id: str) -> bool:
    """Delete a model configuration."""
    models = load_models_config()
    
    for i, model in enumerate(models):
        if model['id'] == model_id:
            models.pop(i)
            models = ensure_default_model(models)
            save_models_config(models)
            return True
    
    return False
