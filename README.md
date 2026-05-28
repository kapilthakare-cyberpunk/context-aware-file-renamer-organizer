# Context-Aware File Organizer

A Python utility that automatically organizes files into categorized folders while protecting important system and configuration files.

## Features

- **Smart categorization**: Automatically sorts files by extension (Images, Documents, Videos, Audio, Code, Archives, etc.)
- **Protection system**: Never moves critical files like config files (`.zshrc`, `.gitconfig`), system directories, or project folders
- **Dry-run mode**: Preview changes before applying them
- **Recursive organization**: Optionally organize subdirectories
- **Scheduled execution**: Run continuously at configurable intervals or once manually

## Installation

```bash
cd context-aware-file-renamer-organizer
python3 context_aware_organizer.py --help
```

## Usage

### Run once on target directories
```bash
python3 context_aware_organizer.py --run-once
```

### Dry run (preview changes)
```bash
python3 context_aware_organizer.py --dry-run --run-once
```

### Organize a specific directory
```bash
python3 context_aware_organizer.py --target /path/to/directory --run-once
```

### Recursive organization
```bash
python3 context_aware_organizer.py --target ~/Downloads --recursive --run-once
```

### Continuous mode (default)
```bash
python3 context_aware_organizer.py
# Runs every 3 hours by default
```

## Configuration

Configuration is stored at `~/.file_organizer_config.json`. Default settings can be overridden:

- `target_dirs`: List of directories to organize
- `categories`: File extension to category mapping
- `important_patterns`: Files/folders to protect from moving
- `hidden_exceptions`: Hidden files that are safe to move (like `.DS_Store`)
- `recursive`: Whether to organize subdirectories
- `dry_run`: Preview mode without actual moves
- `run_interval_hours`: Hours between organization cycles

## Protected Files

The organizer protects:
- Hidden config files (`.zshrc`, `.bashrc`, `.ssh`, etc.) 
- System directories (`System`, `Library`, `Applications`)
- Cloud sync folders (`Dropbox`, `Google Drive`, `OneDrive`)
- Project folders (`node_modules`, `.git`, `.svn`)
- README and LICENSE files

## Testing

```bash
python3 test_organizer.py
```

## Requirements

- Python 3.6+
- Standard library only (no external dependencies)