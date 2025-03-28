import os
from PyQt6.QtCore import QThread, pyqtSignal
from .file_utils import get_folder_size, get_file_stats, format_size

class DirectoryScanner(QThread):
    progress = pyqtSignal(str, int)  # path, progress
    finished = pyqtSignal(dict)      # results
    error = pyqtSignal(str)          # error message

    def __init__(self, root_path):
        super().__init__()
        self.root_path = root_path
        self.canceled = False

    def run(self):
        try:
            if not os.path.isdir(self.root_path):
                self.error.emit("Invalid directory path")
                return

            results = {
                'structure': [],
                'total_size': 0,
                'file_count': 0,
                'folder_count': 0,
                'root_name': os.path.basename(self.root_path),
                'root_size': get_folder_size(self.root_path)
            }

            # First pass: count files/folders and calculate total size
            for root, dirs, files in os.walk(self.root_path):
                if self.canceled:
                    return
                
                results['folder_count'] += len(dirs)
                results['file_count'] += len(files)
                results['total_size'] += sum(
                    os.path.getsize(os.path.join(root, f)) for f in files
                )

            # Second pass: build structure
            self._scan_directory(self.root_path, 0, results)
            self.finished.emit(results)

        except Exception as e:
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
                    results['structure'].append(
                        f"{indent}{prefix}{item}/ {format_size(size)}"
                    )
                    self._scan_directory(full_path, indent_level + 1, results)
                else:
                    size, modified = get_file_stats(full_path)
                    prefix = "└── " if is_last else "├── "
                    indent = "    " * indent_level
                    results['structure'].append(
                        f"{indent}{prefix}{item.ljust(25)} {format_size(size)} 🕒 {modified}"
                    )
                
                # Update progress
                progress = int((i + 1) / len(items) * 100)
                self.progress.emit(full_path, progress)

        except PermissionError:
            indent = "    " * indent_level
            results['structure'].append(f"{indent}└── [Permission denied]")

    def cancel(self):
        self.canceled = True