#!/usr/bin/env python3
"""
Context-Aware File and Folder Organizer
Runs regularly to arrange files and folders without breaking important files.
"""

import os
import sys
import shutil
import json
import time
from pathlib import Path
from datetime import datetime
import logging

# Configuration constants
CONFIG_FILE = Path.home() / '.file_organizer_config.json'
LOG_FILE = Path.home() / '.file_organizer.log'
DEFAULT_TARGET_DIRS = [
    Path.home() / 'Downloads',
    Path.home() / 'Desktop',
    Path.home() / 'Documents',
]

# File organization constants
MAX_CONFLICT_RETRIES = 10
DEFAULT_RUN_INTERVAL_HOURS = 3
SECONDS_PER_HOUR = 3600

# File categories with extensions
CATEGORIES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.webp', '.tiff', '.raw'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages', '.tex'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv', '.tsv', '.ods'],
    'Presentations': ['.ppt', '.pptx', '.key'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz', '.dmg', '.iso'],
    'Videos': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'],
    'Audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'],
    'Code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts'],
    'Scripts': ['.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd'],
    'Executables': ['.exe', '.msi', '.app', '.deb', '.rpm'],
    'Fonts': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
    'Design': ['.psd', '.ai', '.sketch', '.fig', '.xd', '.eps', '.indd'],
    'Others': [],
}

# Important files and folders to never move (protected)
IMPORTANT_PATTERNS = [
    'Applications',
    'Library',
    'System',
    'Users',
    'Volumes',
    '.zshrc',
    '.zprofile',
    '.bash_profile',
    '.bashrc',
    '.gitconfig',
    '.gitignore',
    '.ssh',
    '.gnupg',
    'Application Support',
    'Preferences',
    'Caches',
    'Logs',
    'Dropbox',
    'Google Drive',
    'OneDrive',
    'node_modules',
    '.git',
    '.svn',
    '.hg',
    'LICENSE',
    'README',
    'README.md',
    'README.txt',
    'CONTRIBUTING',
]

HIDDEN_EXCEPTIONS = ['.DS_Store', '.localized']

SYSTEM_PATHS = {'System', 'Library', 'Applications', '/usr', '/bin', '/sbin', '/etc'}


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler(sys.stdout)
        ]
    )


def load_config():
    """Load configuration from file or create default."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"Invalid JSON in config file {CONFIG_FILE}: {e}")
        except PermissionError as e:
            logging.error(f"Permission denied reading config {CONFIG_FILE}: {e}")
    
    config = {
        'target_dirs': [str(p) for p in DEFAULT_TARGET_DIRS],
        'categories': CATEGORIES,
        'important_patterns': IMPORTANT_PATTERNS,
        'hidden_exceptions': HIDDEN_EXCEPTIONS,
        'recursive': False,
        'dry_run': False,
        'run_interval_hours': DEFAULT_RUN_INTERVAL_HOURS,
    }
    save_config(config)
    return config


def save_config(config):
    """Save configuration to file."""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        logging.info(f"Configuration saved to {CONFIG_FILE}")
    except PermissionError as e:
        logging.error(f"Permission denied writing config to {CONFIG_FILE}: {e}")
    except OSError as e:
        logging.error(f"Failed to write config to {CONFIG_FILE}: {e}")


def is_hidden_config_file(file_path, config):
    """Check if file is a hidden config file that should be protected."""
    name = file_path.name
    if not name.startswith('.'):
        return False
    return name not in config['hidden_exceptions']


def matches_important_pattern(file_path, config):
    """Check if file matches any important pattern to protect."""
    name = file_path.name
    for pattern in config['important_patterns']:
        if pattern == name and not pattern.endswith('/'):
            return True
        if pattern.endswith('/') and file_path.is_dir() and name == pattern.rstrip('/'):
            return True
    return False


def is_in_system_path(file_path):
    """Check if file is in a system-critical path that should be protected."""
    try:
        return any(part in SYSTEM_PATHS for part in file_path.parts)
    except (TypeError, AttributeError):
        return False


def is_important_file(file_path, config):
    """
    Check if a file or folder is important and should not be moved.
    Returns True if important (should skip), False otherwise.
    """
    path = Path(file_path)
    
    if is_hidden_config_file(path, config):
        return True
    
    if matches_important_pattern(path, config):
        return True
    
    if is_in_system_path(path):
        return True
    
    return False


def get_category_for_file(file_path, config):
    """
    Determine the category for a file based on its extension.
    Returns category name or 'Others'.
    """
    path = Path(file_path)
    ext = path.suffix.lower()
    
    for category, extensions in config['categories'].items():
        if ext in extensions:
            return category
    
    return 'Others'


def get_items_to_organize(target_path, recursive):
    """Get list of files to organize from target directory."""
    try:
        if recursive:
            return list(target_path.rglob('*'))
        return list(target_path.iterdir())
    except PermissionError as e:
        logging.error(f"Permission denied accessing {target_path}: {e}")
        return []


def resolve_destination_path(item, target_path, category, dry_run):
    """
    Resolve destination path with conflict handling.
    Returns (dest_path, skipped) tuple.
    """
    category_dir = target_path / category
    
    if not dry_run:
        category_dir.mkdir(exist_ok=True)
    
    dest = category_dir / item.name
    counter = 1
    
    while dest.exists():
        stem = item.stem
        suffix = item.suffix
        dest = category_dir / f"{stem}_{counter}{suffix}"
        counter += 1
        
        if counter > MAX_CONFLICT_RETRIES:
            logging.warning(f"Too many conflicts for {item.name}, skipping")
            return None, True
    
    return dest, False


def move_file(item, dest, dry_run):
    """Move file to destination, handling errors with context."""
    if dry_run:
        logging.info(f"[DRY RUN] Would move: {item} -> {dest}")
        return
    
    try:
        shutil.move(str(item), str(dest))
        logging.info(f"Moved: {item.name} -> {dest.parent.name}/")
    except PermissionError as e:
        logging.error(f"Permission denied moving {item}: {e}")
    except OSError as e:
        logging.error(f"Failed to move {item} to {dest}: {e}")


def organize_directory(target_dir, config):
    """Organize files in the target directory."""
    target_path = Path(target_dir)
    
    if not target_path.exists():
        logging.warning(f"Target directory does not exist: {target_dir}")
        return
    if not target_path.is_dir():
        logging.warning(f"Target path is not a directory: {target_dir}")
        return
    
    logging.info(f"Organizing directory: {target_dir}")
    
    items = get_items_to_organize(target_path, config.get('recursive', False))
    dry_run = config.get('dry_run', False)
    
    for item in items:
        if is_important_file(item, config):
            logging.debug(f"Skipping important item: {item}")
            continue
        
        if item.is_dir():
            continue
        
        category = get_category_for_file(item, config)
        dest, skipped = resolve_destination_path(item, target_path, category, dry_run)
        
        if not skipped:
            move_file(item, dest, dry_run)


def run_once(config):
    """Execute a single organization pass on all target directories."""
    for target_dir in config['target_dirs']:
        organize_directory(target_dir, config)
    logging.info("Organization complete.")


def run_continuous(config):
    """Run file organization continuously at configured intervals."""
    interval_hours = config.get('run_interval_hours', DEFAULT_RUN_INTERVAL_HOURS)
    interval_seconds = interval_hours * SECONDS_PER_HOUR
    
    logging.info(f"Starting file organizer. Will run every {interval_hours} hours.")
    logging.info(f"Target directories: {config['target_dirs']}")
    
    while True:
        start_time = time.time()
        run_once(config)
        
        elapsed = time.time() - start_time
        sleep_time = max(0, interval_seconds - elapsed)
        
        logging.info(f"Organization cycle completed in {elapsed:.2f} seconds. "
                    f"Next run in {sleep_time/SECONDS_PER_HOUR:.2f} hours.")
        
        time.sleep(sleep_time)


def main():
    """Main entry point for the file organizer."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Context-Aware File and Folder Organizer')
    parser.add_argument('--target', type=str, help='Target directory to organize (overrides config)')
    parser.add_argument('--recursive', action='store_true', help='Organize recursively')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without moving')
    parser.add_argument('--configure', action='store_true', help='Configure the organizer')
    parser.add_argument('--run-once', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    setup_logging()
    config = load_config()
    
    if args.configure:
        print(f"Configuration mode not implemented. Edit {CONFIG_FILE} directly.")
        return
    
    if args.target:
        config['target_dirs'] = [args.target]
    if args.recursive:
        config['recursive'] = True
    if args.dry_run:
        config['dry_run'] = True
    
    if args.run_once:
        run_once(config)
    else:
        run_continuous(config)


if __name__ == '__main__':
    main()