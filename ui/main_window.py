import os
from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QLabel, 
                            QLineEdit, QPushButton, QHBoxLayout, QScrollArea,
                            QFrame, QFileDialog, QProgressBar)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon
from core.directory_scanner import DirectoryScanner
from core.file_utils import format_size

class DirectoryVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Directory Structure Visualizer")
        self.setMinimumSize(800, 600)
        self.scanner = None
        self.init_ui()
        self.apply_styles()

    def init_ui(self):
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(15)

        # Input Section
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText("Enter directory path...")
        
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browse_directory)
        
        self.scan_btn = QPushButton("Scan")
        self.scan_btn.clicked.connect(self.start_scan)
        self.scan_btn.setStyleSheet("background-color: #0078d7;")
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.cancel_scan)
        self.cancel_btn.setEnabled(False)
        
        input_layout.addWidget(QLabel("Directory:"))
        input_layout.addWidget(self.dir_input, 1)
        input_layout.addWidget(self.browse_btn)
        input_layout.addWidget(self.scan_btn)
        input_layout.addWidget(self.cancel_btn)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setTextVisible(False)
        
        # Results Display
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        
        self.scroll_area.setWidget(self.content_widget)
        
        # Status Bar
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Add to main layout
        layout.addWidget(input_frame)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.scroll_area, 1)
        layout.addWidget(self.status_label)

        # Set initial directory
        self.dir_input.setText(os.getcwd())

    def apply_styles(self):
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
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QFrame {
                background-color: #3d3d3d;
                border-radius: 4px;
                border: 1px solid #555;
            }
            QProgressBar {
                border: 1px solid #555;
                border-radius: 3px;
                text-align: center;
                background: #3d3d3d;
            }
            QProgressBar::chunk {
                background: #0078d7;
                width: 10px;
            }
        """)

    def browse_directory(self):
        path = QFileDialog.getExistingDirectory(self, "Select Directory")
        if path:
            self.dir_input.setText(path)

    def start_scan(self):
        if self.scanner and self.scanner.isRunning():
            return
            
        self.clear_results()
        path = self.dir_input.text()
        
        if not path or not os.path.isdir(path):
            self.show_error("Invalid directory path")
            return
        
        self.scanner = DirectoryScanner(path)
        self.scanner.progress.connect(self.update_progress)
        self.scanner.finished.connect(self.show_results)
        self.scanner.error.connect(self.show_error)
        
        self.scan_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.status_label.setText("Scanning...")
        self.progress_bar.setValue(0)
        
        self.scanner.start()

    def cancel_scan(self):
        if self.scanner and self.scanner.isRunning():
            self.scanner.cancel()
            self.scanner.wait()
        self.reset_ui()
        self.status_label.setText("Scan canceled")

    def update_progress(self, path, value):
        self.progress_bar.setValue(value)
        self.status_label.setText(f"Scanning: {os.path.basename(path)}...")

    def show_results(self, results):
        self.progress_bar.setValue(100)
        
        # Add root summary
        root_label = QLabel(
            f"{results['root_name']}/  {format_size(results['root_size'])}"
        )
        root_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px 0;")
        self.content_layout.addWidget(root_label)
        
        # Add summary
        summary = QLabel(
            f"📂 {results['folder_count']} folders | "
            f"📄 {results['file_count']} files | "
            f"🗃️ {format_size(results['total_size'])}"
        )
        summary.setStyleSheet("font-weight: bold; padding: 5px 0;")
        self.content_layout.addWidget(summary)
        
        # Add structure
        for line in results['structure']:
            label = QLabel(line)
            label.setStyleSheet("font-family: monospace;")
            self.content_layout.addWidget(label)
        
        self.status_label.setText("Scan completed")
        self.reset_ui()

    def show_error(self, message):
        label = QLabel(f"Error: {message}")
        label.setStyleSheet("color: #ff5555;")
        self.content_layout.addWidget(label)
        self.status_label.setText("Error occurred")
        self.reset_ui()

    def clear_results(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def reset_ui(self):
        self.scan_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        if self.scanner:
            self.scanner.deleteLater()
            self.scanner = None