"""Tests for parse cache manager."""

import json
import os
import time
from pathlib import Path
import tempfile
import pytest

from src.utils.parse_cache import ParseCacheManager


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def cache_file(temp_dir):
    """Create a temporary cache file path."""
    return str(temp_dir / "test_cache.json")


@pytest.fixture
def input_dir(temp_dir):
    """Create a temporary input directory with test files."""
    input_path = temp_dir / "input"
    input_path.mkdir()
    
    # Create test PDF file
    pdf_file = input_path / "test.pdf"
    pdf_file.write_text("dummy pdf content")
    
    # Create test markdown file
    md_file = input_path / "test.md"
    md_file.write_text("# Test\n\nSome content")
    
    return str(input_path)


@pytest.fixture
def output_file(temp_dir):
    """Create a temporary output file."""
    output_path = temp_dir / "output.md"
    output_path.write_text("# Generated Output\n\nTest content")
    return str(output_path)


@pytest.fixture
def test_config():
    """Test configuration."""
    return {
        "llm_model": "databricks-gpt-5-2",
        "vision_model": "databricks-claude-sonnet-4",
        "use_llm": True,
        "domain": "combined"
    }


class TestParseCacheManager:
    """Test ParseCacheManager functionality."""
    
    def test_cache_creation_and_saving(self, cache_file, input_dir, output_file, test_config):
        """Test that cache can be created and saved."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        result = manager.save(output_file, input_dir, test_config)
        assert result is True
        
        # Verify cache file exists
        assert Path(cache_file).exists()
        
        # Load and verify contents
        with open(cache_file, 'r') as f:
            cache_data = json.load(f)
        
        assert cache_data["version"] == ParseCacheManager.VERSION
        assert cache_data["output_path"] == output_file
        assert cache_data["config"] == test_config
        assert "timestamp" in cache_data
        assert "input_files" in cache_data
        assert len(cache_data["input_files"]) == 2  # PDF + MD
    
    def test_cache_validation_with_unchanged_files(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache validates correctly when files haven't changed."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Wait a moment to ensure no timing issues
        time.sleep(0.1)
        
        # Validate cache (should be valid)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is True
    
    def test_cache_invalidation_when_file_modified(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalidated when input file is modified."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Wait to ensure mtime changes
        time.sleep(1.5)
        
        # Modify an input file
        pdf_file = Path(input_dir) / "test.pdf"
        pdf_file.write_text("modified pdf content")
        
        # Validate cache (should be invalid)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_invalidation_when_file_added(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalidated when a new file is added."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Add a new file
        new_file = Path(input_dir) / "new_file.pdf"
        new_file.write_text("new content")
        
        # Validate cache (should be invalid)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_invalidation_when_file_removed(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalidated when a file is removed."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Remove a file
        pdf_file = Path(input_dir) / "test.pdf"
        pdf_file.unlink()
        
        # Validate cache (should be invalid)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_invalidation_when_config_changes(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalidated when config changes."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Change config
        new_config = test_config.copy()
        new_config["llm_model"] = "databricks-gpt-4"
        
        # Validate cache (should be invalid)
        assert manager.is_valid(output_file, input_dir, new_config, verbose=False) is False
    
    def test_cache_invalidation_when_output_missing(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalidated when output file is missing."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Remove output file
        Path(output_file).unlink()
        
        # Validate cache (should be invalid)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_invalid_when_no_cache_file(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that validation fails when cache file doesn't exist."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Don't save cache - just validate
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_invalidation_method(self, cache_file, input_dir, output_file, test_config):
        """Test manual cache invalidation."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        assert Path(cache_file).exists()
        
        # Invalidate cache
        result = manager.invalidate()
        assert result is True
        assert not Path(cache_file).exists()
        
        # Invalidate again (should return False since already deleted)
        result = manager.invalidate()
        assert result is False
    
    def test_cache_get_metadata(self, cache_file, input_dir, output_file, test_config):
        """Test retrieving cache metadata."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Before loading
        assert manager.get_metadata() is None
        
        # Save and load
        manager.save(output_file, input_dir, test_config)
        manager.load()
        
        # Get metadata
        metadata = manager.get_metadata()
        assert metadata is not None
        assert metadata["version"] == ParseCacheManager.VERSION
        assert metadata["output_path"] == output_file
        assert metadata["config"] == test_config
    
    def test_cache_handles_corrupted_file(self, cache_file, input_dir, output_file, test_config):
        """Test that corrupted cache file is handled gracefully."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Create corrupted cache file
        Path(cache_file).write_text("invalid json {{{")
        
        # Load should fail gracefully
        result = manager.load()
        assert result is False
        assert manager.get_metadata() is None
        
        # Validation should fail
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_with_empty_input_dir(self, cache_file, temp_dir, output_file, test_config):
        """Test cache behavior with empty input directory."""
        # Create empty input directory
        empty_dir = temp_dir / "empty"
        empty_dir.mkdir()
        
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache with empty dir
        result = manager.save(output_file, str(empty_dir), test_config)
        assert result is True
        
        # Validate (should be valid)
        assert manager.is_valid(output_file, str(empty_dir), test_config, verbose=False) is True
    
    def test_cache_tracks_file_size(self, cache_file, input_dir, output_file, test_config):
        """Test that cache tracks file sizes."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache
        manager.save(output_file, input_dir, test_config)
        
        # Wait to ensure mtime changes
        time.sleep(1.5)
        
        # Change file size (write different content)
        pdf_file = Path(input_dir) / "test.pdf"
        original_size = pdf_file.stat().st_size
        pdf_file.write_text("much longer pdf content with more data")
        new_size = pdf_file.stat().st_size
        
        # Ensure size actually changed
        assert new_size != original_size
        
        # Validate cache (should be invalid due to size change)
        assert manager.is_valid(output_file, input_dir, test_config, verbose=False) is False
    
    def test_cache_with_different_output_path(
        self, cache_file, input_dir, output_file, test_config
    ):
        """Test that cache is invalid when output path changes."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Save cache with one output path
        manager.save(output_file, input_dir, test_config)
        
        # Create different output file
        different_output = str(Path(output_file).parent / "different_output.md")
        Path(different_output).write_text("different output")
        
        # Validate with different output path (should be invalid)
        assert manager.is_valid(different_output, input_dir, test_config, verbose=False) is False


class TestParseCacheVerboseMode:
    """Test verbose output of cache validation."""
    
    def test_verbose_mode_shows_reasons(
        self, cache_file, input_dir, output_file, test_config, capsys
    ):
        """Test that verbose mode shows validation failure reasons."""
        manager = ParseCacheManager(cache_file=cache_file)
        
        # Test 1: No cache file
        manager.is_valid(output_file, input_dir, test_config, verbose=True)
        captured = capsys.readouterr()
        assert "No cache file found" in captured.out
        
        # Test 2: Config change
        manager.save(output_file, input_dir, test_config)
        new_config = test_config.copy()
        new_config["domain"] = "different"
        manager.is_valid(output_file, input_dir, new_config, verbose=True)
        captured = capsys.readouterr()
        assert "Configuration changed" in captured.out
        
        # Test 3: File added
        new_file = Path(input_dir) / "added.md"
        new_file.write_text("added content")
        manager.is_valid(output_file, input_dir, test_config, verbose=True)
        captured = capsys.readouterr()
        assert "Files added" in captured.out or "File" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
