"""
Tests for HistoryManager
"""
import pytest
from flatshot.utils.history_manager import HistoryManager
from flatshot.core.models import ShadowSettings


class TestHistoryManager:
    """Tests for the HistoryManager class."""
    
    @pytest.fixture
    def history(self):
        """Create a fresh history manager."""
        return HistoryManager(max_history=5)
    
    def test_initial_state(self, history):
        """Test initial empty state."""
        assert not history.can_undo()
        assert not history.can_redo()
        assert history.history_size == 0
    
    def test_push_single(self, history):
        """Test pushing a single state."""
        settings = ShadowSettings(angle=90)
        history.push(settings)
        
        assert history.history_size == 1
        assert not history.can_undo()  # Can't undo with just one state
        assert not history.can_redo()
    
    def test_push_multiple(self, history):
        """Test pushing multiple states."""
        history.push(ShadowSettings(angle=0))
        history.push(ShadowSettings(angle=90))
        history.push(ShadowSettings(angle=180))
        
        assert history.history_size == 3
        assert history.can_undo()
        assert not history.can_redo()
    
    def test_undo(self, history):
        """Test undo operation."""
        history.push(ShadowSettings(angle=0))
        history.push(ShadowSettings(angle=90))
        history.push(ShadowSettings(angle=180))
        
        # Currently at angle=180
        result = history.undo()
        assert result is not None
        assert result.angle == 90
        
        result = history.undo()
        assert result is not None
        assert result.angle == 0
    
    def test_redo(self, history):
        """Test redo operation."""
        history.push(ShadowSettings(angle=0))
        history.push(ShadowSettings(angle=90))
        history.push(ShadowSettings(angle=180))
        
        # Undo twice
        history.undo()
        history.undo()
        
        # Now redo
        result = history.redo()
        assert result is not None
        assert result.angle == 90
        
        result = history.redo()
        assert result is not None
        assert result.angle == 180
    
    def test_redo_cleared_on_new_push(self, history):
        """Test that redo history is cleared when new state is pushed."""
        history.push(ShadowSettings(angle=0))
        history.push(ShadowSettings(angle=90))
        history.push(ShadowSettings(angle=180))
        
        # Undo once
        history.undo()
        assert history.can_redo()
        
        # Push new state - should clear redo stack
        history.push(ShadowSettings(angle=270))
        assert not history.can_redo()
    
    def test_max_history_limit(self, history):
        """Test that history is limited to max size."""
        # Push more than max_history (5) items
        for i in range(10):
            history.push(ShadowSettings(angle=i * 10))
        
        # Should be capped at 5
        assert history.history_size == 5
    
    def test_no_duplicate_consecutive(self, history):
        """Test that identical consecutive states are not pushed."""
        settings = ShadowSettings(angle=90)
        history.push(settings)
        history.push(settings)  # Same settings
        history.push(settings)  # Same settings again
        
        assert history.history_size == 1
    
    def test_undo_returns_none_at_beginning(self, history):
        """Test undo returns None when at beginning."""
        history.push(ShadowSettings(angle=0))
        
        result = history.undo()
        assert result is None
    
    def test_redo_returns_none_at_end(self, history):
        """Test redo returns None when at end."""
        history.push(ShadowSettings(angle=0))
        
        result = history.redo()
        assert result is None
    
    def test_clear(self, history):
        """Test clearing history."""
        history.push(ShadowSettings(angle=0))
        history.push(ShadowSettings(angle=90))
        
        history.clear()
        
        assert history.history_size == 0
        assert not history.can_undo()
        assert not history.can_redo()
