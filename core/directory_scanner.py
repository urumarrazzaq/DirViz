import os
from PyQt6.QtCore import QThread, pyqtSignal
from .file_utils import get_folder_size, get_file_stats, format_size
from datetime import datetime

class DirectoryScanner(QThread):
    progress = pyqtSignal(str, int)  # path, progress
    finished = pyqtSignal(dict)      # results
    error = pyqtSignal(str)          # error message

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.canceled = False
        self.log_file = "directory_structure.log"
        self.ensure_log_directory()

    def ensure_log_directory(self):
        """Ensure log directory exists"""
        log_dir = os.path.dirname(os.path.abspath(self.log_file))
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)

    def write_to_log(self, content):
        """Safely write Unicode content to log file"""
        try:
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(content + "\n")
        except Exception as e:
            print(f"Failed to write to log: {str(e)}")

    def run(self):
        try:
            # Clear previous log with UTF-8 encoding
            with open(self.log_file, 'w', encoding='utf-8') as f:
                f.write(f"Directory Structure Scan - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if not os.path.isdir(self.root_path):
                error_msg = "Invalid directory path"
                self.write_to_log(f"ERROR: {error_msg}")
                self.error.emit(error_msg)
                return

            results = {
                'structure': [],
                'total_size': 0,
                'file_count': 0,
                'folder_count': 0,
                'root_name': os.path.basename(self.root_path),
                'root_size': get_folder_size(self.root_path)
            }

            # First pass: count files/folders
            for root, dirs, files in os.walk(self.root_path):
                if self.canceled:
                    self.write_to_log("\nScan canceled by user")
                    return
                
                results['folder_count'] += len(dirs)
                results['file_count'] += len(files)
                results['total_size'] += sum(
                    os.path.getsize(os.path.join(root, f)) for f in files
                )

            # Second pass: build structure and log
            self.write_to_log(f"ROOT: {results['root_name']} ({format_size(results['root_size'])})")
            self._scan_directory(self.root_path, 0, results)
            
            # Write summary
            summary = (
                f"\nSCAN SUMMARY:\n"
                f"Files: {results['file_count']}\n"
                f"Folders: {results['folder_count']}\n"
                f"Total Size: {format_size(results['total_size'])}\n"
                f"Scan completed at {datetime.now().strftime('%H:%M:%S')}"
            )
            self.write_to_log(summary)
            self.finished.emit(results)

        except Exception as e:
            self.write_to_log(f"\nFATAL ERROR: {str(e)}")
            self.error.emit(str(e))

    def _scan_directory(self, path, indent_level, results):
        try:
            items = sorted(os.listdir(path),
                         key=lambda x: (not os.path.isdir(os.path.join(path, x)), x.lower()))
            
            for i, item in enumerate(items):
                if self.canceled:
                    return
                
                full_path = os.path.join(path, item)
                is_last = i == len(items) - 1
                
                if os.path.isdir(full_path):
                    size = get_folder_size(full_path)
                    prefix = "└── " if is_last else "├── "
                    indent = "    " * indent_level
                    line = f"{indent}{prefix}{item}/ {format_size(size)}"
                    results['structure'].append((line, False))
                    self.write_to_log(line)
                    self._scan_directory(full_path, indent_level + 1, results)
                else:
                    size, modified, is_large = get_file_stats(full_path)
                    prefix = "└── " if is_last else "├── "
                    indent = "    " * indent_level
                    line = f"{indent}{prefix}{item.ljust(25)} {format_size(size)} 🕒 {modified}"
                    results['structure'].append((line, is_large))
                    self.write_to_log(line)
                
                progress = int((i + 1) / len(items) * 100)
                self.progress.emit(full_path, progress)

        except PermissionError:
            indent = "    " * indent_level
            error_line = f"{indent}└── [Permission denied]"
            results['structure'].append((error_line, False))
            self.write_to_log(error_line)

    def cancel(self):
        self.canceled = True