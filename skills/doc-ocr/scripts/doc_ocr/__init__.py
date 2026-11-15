"""Unified OCR routing for the lecture digitization workflow."""

from .router import DocumentProfile, RouteDecision, choose_backends

__all__ = ["DocumentProfile", "RouteDecision", "choose_backends"]
