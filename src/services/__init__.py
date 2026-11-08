"""
Services layer for the Romanian Text Processor.
Contains service classes for external integrations and utilities.
"""

from .ollama_service import OllamaService, get_ollama_service

__all__ = ['OllamaService', 'get_ollama_service']