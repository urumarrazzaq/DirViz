import os
from datetime import datetime

from config.config import MAX_FILE_SIZE_KB


def format_size(size):
    """Convert size to human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            if unit == 'B':
                return f"{size:.0f}{unit}"
            return f"{size:.1f}{unit}"
        size /= 1024.0
    return f"{size:.1f}PB"

def get_file_stats(path):
    """Get file size and modified time with size check"""
    try:
        size = os.path.getsize(path)
        modified = datetime.fromtimestamp(os.path.getmtime(path)).strftime('%Y-%m-%d %H:%M')
        is_large = size > MAX_FILE_SIZE_KB * 1024  # Convert KB to bytes
        return size, modified, is_large
    except Exception:
        return 0, "Unknown", False

def get_folder_size(path):
    """Calculate total size of a folder"""
    total = 0
    try:
        with os.scandir(path) as it:
            for entry in it:
                if entry.is_file():
                    total += entry.stat().st_size
                elif entry.is_dir():
                    total += get_folder_size(entry.path)
    except PermissionError:
        pass
    return total