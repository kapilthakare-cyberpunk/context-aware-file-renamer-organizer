#!/usr/bin/env python3
"""Simple tests without pytest dependency."""

import os
import tempfile
import shutil
from pathlib import Path

# Import functions from the main module
import sys
sys.path.insert(0, str(Path(__file__).parent))
from context_aware_organizer import (
    is_important_file,
    is_hidden_config_file,
    matches_important_pattern,
    is_in_system_path,
    get_category_for_file,
    resolve_destination_path,
    organize_directory,
    MAX_CONFLICT_RETRIES,
)


def test_is_hidden_config_file():
    """Test hidden config file detection."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {'hidden_exceptions': ['.DS_Store']}
        
        ds_store = tmp_path / '.DS_Store'
        ds_store.touch()
        assert is_hidden_config_file(ds_store, config) is False
        
        zshrc = tmp_path / '.zshrc'
        zshrc.touch()
        assert is_hidden_config_file(zshrc, config) is True
        
        regular = tmp_path / 'regular.txt'
        regular.touch()
        assert is_hidden_config_file(regular, config) is False
    print("✓ test_is_hidden_config_file passed")


def test_matches_important_pattern():
    """Test important pattern matching."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {'important_patterns': ['README.md', 'LICENSE']}
        
        readme = tmp_path / 'README.md'
        readme.touch()
        assert matches_important_pattern(readme, config) is True
        
        node_modules = tmp_path / 'node_modules'
        node_modules.mkdir()
        config2 = {'important_patterns': ['node_modules']}
        assert matches_important_pattern(node_modules, config2) is True
        
        other = tmp_path / 'other.txt'
        other.touch()
        assert matches_important_pattern(other, config) is False
    print("✓ test_matches_important_pattern passed")


def test_is_in_system_path():
    """Test system path detection."""
    assert is_in_system_path(Path('/System/Library/somefile')) is True
    
    with tempfile.TemporaryDirectory() as tmpdir:
        regular = Path(tmpdir) / 'regular.txt'
        assert is_in_system_path(regular) is False
    print("✓ test_is_in_system_path passed")


def test_get_category_for_file():
    """Test file categorization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {
            'categories': {
                'Images': ['.jpg', '.png'],
                'Documents': ['.pdf'],
            }
        }
        
        jpg_file = tmp_path / 'photo.jpg'
        assert get_category_for_file(jpg_file, config) == 'Images'
        
        PNG_file = tmp_path / 'PHOTO.PNG'
        assert get_category_for_file(PNG_file, config) == 'Images'
        
        unknown = tmp_path / 'file.xyz'
        assert get_category_for_file(unknown, config) == 'Others'
    print("✓ test_get_category_for_file passed")


def test_resolve_destination_path():
    """Test destination path resolution with conflict handling."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        
        new_file = tmp_path / 'new.pdf'
        new_file.touch()
        dest, skipped = resolve_destination_path(new_file, tmp_path, 'Documents', False)
        assert skipped is False
        assert dest == tmp_path / 'Documents' / 'new.pdf'
        
        category_dir = tmp_path / 'Images'
        category_dir.mkdir()
        existing = category_dir / 'photo.jpg'
        existing.touch()
        
        photo_file = tmp_path / 'photo.jpg'
        photo_file.touch()
        dest, skipped = resolve_destination_path(photo_file, tmp_path, 'Images', False)
        assert skipped is False
        assert dest == category_dir / 'photo_1.jpg'
    print("✓ test_resolve_destination_path passed")


def test_organization_dry_run():
    """Test dry run mode doesn't move files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {
            'hidden_exceptions': [],
            'important_patterns': [],
            'categories': {'Images': ['.jpg']},
            'dry_run': True,
            'recursive': False,
        }
        
        test_image = tmp_path / 'test.jpg'
        test_image.touch()
        
        organize_directory(tmp_path, config)
        
        assert test_image.exists()
        assert not (tmp_path / 'Images').exists()
    print("✓ test_organization_dry_run passed")


def test_organization_moves_files():
    """Test organization actually moves files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {
            'hidden_exceptions': [],
            'important_patterns': [],
            'categories': {'Images': ['.jpg']},
            'dry_run': False,
            'recursive': False,
        }
        
        test_image = tmp_path / 'test.jpg'
        test_image.touch()
        
        organize_directory(tmp_path, config)
        
        assert not test_image.exists()
        assert (tmp_path / 'Images' / 'test.jpg').exists()
    print("✓ test_organization_moves_files passed")


def test_protected_files_not_moved():
    """Test that protected files are not moved."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        config = {
            'hidden_exceptions': [],
            'important_patterns': ['important.txt'],
            'categories': {'Documents': ['.txt']},
            'dry_run': False,
            'recursive': False,
        }
        
        protected_file = tmp_path / 'important.txt'
        protected_file.touch()
        
        organize_directory(tmp_path, config)
        
        assert protected_file.exists()
        assert not (tmp_path / 'Documents').exists()
    print("✓ test_protected_files_not_moved passed")


def run_all_tests():
    """Run all tests."""
    print("Running tests...\n")
    test_is_hidden_config_file()
    test_matches_important_pattern()
    test_is_in_system_path()
    test_get_category_for_file()
    test_resolve_destination_path()
    test_organization_dry_run()
    test_organization_moves_files()
    test_protected_files_not_moved()
    print("\n✓ All tests passed!")


if __name__ == '__main__':
    run_all_tests()