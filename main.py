import os
import sys
from pathlib import Path

try:
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QTreeView,
                                QVBoxLayout, QWidget, QLabel, QLineEdit, QPushButton,
                                QHBoxLayout, QSizePolicy, QScrollArea, QFrame, QFileDialog)
    from PyQt6.QtCore import Qt, QSize, QDir
    from PyQt6.QtGui import QFont, QIcon, QPalette, QColor
    QT_AVAILABLE = True
except ImportError as e:
    QT_AVAILABLE = False
    print(f"PyQt6 import error: {e}")
    print("Please install PyQt6 with: pip install PyQt6")


class DirectoryVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Structure Visualizer")
        self.setMinimumSize(800, 600)
        
        # Set modern style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2d2d2d;
            }
            QLabel {
                color: #f0f0f0;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #3d3d3d;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #4a4a4a;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 4px;
                padding: 5px 15px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #5a5a5a;
            }
            QPushButton:pressed {
                background-color: #3a3a3a;
            }
            QTreeView {
                background-color: #3d3d3d;
                color: #f0f0f0;
                border: 1px solid #555;
                border-radius: 4px;
                font-family: 'Consolas', 'Monospace';
                font-size: 14px;
            }
            QTreeView::item {
                padding: 5px;
            }
            QTreeView::item:hover {
                background-color: #4a4a4a;
            }
            QTreeView::item:selected {
                background-color: #0078d7;
                color: white;
            }
            QHeaderView::section {
                background-color: #4a4a4a;
                color: #f0f0f0;
                padding: 5px;
                border: 1px solid #555;
            }
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QFrame {
                background-color: #3d3d3d;
                border-radius: 4px;
                border: 1px solid #555;
            }
        """)
        
        self.init_ui()
        
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)
        
        # Directory input section
        input_frame = QFrame()
        input_frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(10, 10, 10, 10)
        
        self.dir_label = QLabel("Directory Path:")
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Enter directory path or click 'Browse'...")
        self.browse_button = QPushButton("Browse")
        self.browse_button.clicked.connect(self.browse_directory)
        self.visualize_button = QPushButton("Visualize")
        self.visualize_button.clicked.connect(self.visualize_directory)
        self.visualize_button.setStyleSheet("background-color: #0078d7;")
        
        input_layout.addWidget(self.dir_label)
        input_layout.addWidget(self.dir_input, 1)
        input_layout.addWidget(self.browse_button)
        input_layout.addWidget(self.visualize_button)
        
        # Structure display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.structure_widget = QWidget()
        self.structure_layout = QVBoxLayout(self.structure_widget)
        self.structure_layout.setContentsMargins(0, 0, 0, 0)
        self.structure_layout.setSpacing(0)
        
        self.scroll_area.setWidget(self.structure_widget)
        
        # Add widgets to main layout
        layout.addWidget(input_frame)
        layout.addWidget(self.scroll_area, 1)
        
        # Set initial directory to current working directory
        self.dir_input.setText(os.getcwd())
        self.visualize_directory()
    
    def browse_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if dir_path:
            self.dir_input.setText(dir_path)
            self.visualize_directory()
    
    def visualize_directory(self):
        # Clear previous visualization
        while self.structure_layout.count():
            child = self.structure_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        dir_path = self.dir_input.text()
        if not dir_path or not os.path.isdir(dir_path):
            error_label = QLabel("Invalid directory path. Please select a valid directory.")
            error_label.setStyleSheet("color: #ff5555; font-size: 14px;")
            self.structure_layout.addWidget(error_label)
            return
        
        # Get directory structure
        try:
            root_name = os.path.basename(dir_path)
            root_size = self.get_folder_size(dir_path)
            root_label = QLabel(f"{root_name}/  {self.format_size(root_size)}")
            root_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
            self.structure_layout.addWidget(root_label)
            
            self.display_directory_structure(dir_path, 1)
        except Exception as e:
            error_label = QLabel(f"Error reading directory: {str(e)}")
            error_label.setStyleSheet("color: #ff5555; font-size: 14px;")
            self.structure_layout.addWidget(error_label)
    
    def display_directory_structure(self, dir_path, indent_level):
        try:
            items = sorted(os.listdir(dir_path), key=lambda x: (not os.path.isdir(os.path.join(dir_path, x)), x.lower()))
            
            for i, item in enumerate(items):
                full_path = os.path.join(dir_path, item)
                is_last = i == len(items) - 1
                
                if os.path.isdir(full_path):
                    # Directory
                    dir_size = self.get_folder_size(full_path)
                    prefix = "└── " if is_last else "├── "
                    indent = "    " * (indent_level - 1) + ("│   " * (indent_level - 1) if indent_level > 1 else "")
                    
                    dir_label = QLabel(f"{indent}{prefix}{item}/  {self.format_size(dir_size)}")
                    dir_label.setStyleSheet("padding: 2px 0;")
                    self.structure_layout.addWidget(dir_label)
                    
                    # Recursively display subdirectories
                    self.display_directory_structure(full_path, indent_level + 1)
                else:
                    # File
                    file_size = os.path.getsize(full_path)
                    prefix = "└── " if is_last else "├── "
                    indent = "    " * (indent_level - 1) + ("│   " * (indent_level - 1) if indent_level > 1 else "")
                    
                    file_label = QLabel(f"{indent}{prefix}{item.ljust(30)}  {self.format_size(file_size)}")
                    file_label.setStyleSheet("padding: 2px 0;")
                    self.structure_layout.addWidget(file_label)
        except PermissionError:
            error_label = QLabel(f"{'    ' * indent_level}└── [Permission denied]")
            error_label.setStyleSheet("color: #ff5555; padding: 2px 0;")
            self.structure_layout.addWidget(error_label)
    
    def get_folder_size(self, path):
        total = 0
        try:
            with os.scandir(path) as it:
                for entry in it:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += self.get_folder_size(entry.path)
        except PermissionError:
            pass
        return total
    
    def format_size(self, size):
        # Convert size to human-readable format
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                if unit == 'B':
                    return f"{size:.0f}{unit}"
                else:
                    return f"{size:.1f}{unit}"
            size /= 1024.0
        return f"{size:.1f}PB"

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Set application style and font
    app.setStyle('Fusion')
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = DirectoryVisualizer()
    window.show()
    sys.exit(app.exec())