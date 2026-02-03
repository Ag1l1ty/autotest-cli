"""Registry for language detectors with plugin support."""

from __future__ import annotations

from typing import Type

from autotest.detector.base import BaseLanguageDetector

_REGISTRY: dict[str, Type[BaseLanguageDetector]] = {}


def register(language: str):
    """Decorator to register a language detector."""
    def decorator(cls: Type[BaseLanguageDetector]) -> Type[BaseLanguageDetector]:
        _REGISTRY[language] = cls
        return cls
    return decorator


def get_all_detectors() -> dict[str, Type[BaseLanguageDetector]]:
    """Return all registered detectors."""
    return dict(_REGISTRY)


def get_detector(language: str) -> Type[BaseLanguageDetector] | None:
    """Get a specific detector by language name."""
    return _REGISTRY.get(language)
