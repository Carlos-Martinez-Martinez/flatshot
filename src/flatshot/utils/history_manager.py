"""
History Manager for FlatShot
Handles undo/redo functionality for shadow settings.
"""
from typing import Optional
from flatshot.core.models import (
    SHADOW_ENGINE_COMPAT,
    ShadowSettings,
    normalize_shadow_settings,
)


class HistoryManager:
    """Manages undo/redo history for shadow settings."""
    
    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self._history: list[dict] = []
        self._current_index: int = -1
        self._is_restoring: bool = False  # Flag to prevent recording during undo/redo
    
    def push(self, settings: ShadowSettings):
        """
        Push a new settings state to history.
        Call this when user releases a slider or makes a discrete change.
        """
        if self._is_restoring:
            return
        
        settings_dict = settings.model_dump()
        
        # Don't push if identical to current state
        if self._current_index >= 0:
            if self._history[self._current_index] == settings_dict:
                return
        
        # Remove any redo states (everything after current index)
        if self._current_index < len(self._history) - 1:
            self._history = self._history[:self._current_index + 1]
        
        # Add new state
        self._history.append(settings_dict)
        self._current_index = len(self._history) - 1
        
        # Trim history if too long
        if len(self._history) > self.max_history:
            self._history = self._history[-self.max_history:]
            self._current_index = len(self._history) - 1
    
    def undo(self) -> Optional[ShadowSettings]:
        """
        Undo to previous state.
        Returns the previous ShadowSettings or None if at beginning.
        """
        if not self.can_undo():
            return None
        
        self._current_index -= 1
        self._is_restoring = True
        try:
            return normalize_shadow_settings(
                self._history[self._current_index],
                missing_engine=SHADOW_ENGINE_COMPAT,
            )
        finally:
            self._is_restoring = False
    
    def redo(self) -> Optional[ShadowSettings]:
        """
        Redo to next state.
        Returns the next ShadowSettings or None if at end.
        """
        if not self.can_redo():
            return None
        
        self._current_index += 1
        self._is_restoring = True
        try:
            return normalize_shadow_settings(
                self._history[self._current_index],
                missing_engine=SHADOW_ENGINE_COMPAT,
            )
        finally:
            self._is_restoring = False
    
    def can_undo(self) -> bool:
        """Check if undo is available."""
        return self._current_index > 0
    
    def can_redo(self) -> bool:
        """Check if redo is available."""
        return self._current_index < len(self._history) - 1
    
    def clear(self):
        """Clear all history."""
        self._history.clear()
        self._current_index = -1
    
    def get_current(self) -> Optional[ShadowSettings]:
        """Get current state without changing index."""
        if self._current_index >= 0 and self._current_index < len(self._history):
            return normalize_shadow_settings(
                self._history[self._current_index],
                missing_engine=SHADOW_ENGINE_COMPAT,
            )
        return None
    
    @property
    def history_size(self) -> int:
        """Get current history size."""
        return len(self._history)
    
    @property
    def current_position(self) -> int:
        """Get current position in history (1-indexed for display)."""
        return self._current_index + 1
