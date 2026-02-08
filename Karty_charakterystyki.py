import sys
from pathlib import Path

import fitz  # PyMuPDF
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QMessageBox, QFileDialog, QInputDialog, QLabel, QStyle
)
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from PySide6.QtGui import QPainter, Qt, QIcon
from PySide6.QtCore import QSize

PDF_DIR = Path(r"D:\\Karty_charakterystyki")


class SDSBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wyszukiwarka kart charakterystyki")
        self.resize(1300, 850)

        self.pdf_index = []
        self.current_pdf_path = None
        self.pdf_visible = False

        self._build_ui()
        self._apply_styles()
        self._load_pdfs()

    # ================= IKONY SYSTEMOWE =================
    def sys_icon(self, theme_name, fallback):
        icon = QIcon.fromTheme(theme_name)
        if icon.isNull():
            icon = self.style().standardIcon(fallback)
        return icon

    # ================= UI =================
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        # -------- LEWY PANEL --------
        left_panel = QVBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Szukaj po nazwie karty")
        self.search_input.textChanged.connect(self.search)

        # 🔍 Ikona lupy
        self.search_input.addAction(
            self.sys_icon("edit-find", QStyle.SP_FileDialogContentsView),
            QLineEdit.LeadingPosition
        )

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.open_pdf_from_list)
        self.list_widget.itemDoubleClicked.connect(self.display_pdf_from_list)

        left_panel.addWidget(self.search_input)
        left_panel.addWidget(self.list_widget)

        # -------- PRAWY PANEL --------
        right_panel = QVBoxLayout()

        # ===== NAGŁÓWEK APLIKACJI =====
        self.header_widget = QWidget()
        header_layout = QVBoxLayout(self.header_widget)
        header_layout.setContentsMargins(20, 15, 20, 15)

        self.title_label = QLabel("MSDS Search")
        self.version_label = QLabel("v 1.0")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.version_label.setAlignment(Qt.AlignCenter)

        header_layout.addWidget(self.title_label)
        header_layout.addWidget(self.version_label)

        # Informacje o autorze i prawach zastrzeżonych
        self.copyright_label = QLabel("© 2026 Michal Chojnacki")
        copyright_label = self.copyright_label
        copyright_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(copyright_label)

        # PDF viewer
        self.pdf_document = QPdfDocument(self)
        self.pdf_view = QPdfView()
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.MultiPage)

        # PRZYCISKI
        buttons_layout = QHBoxLayout()

        self.choose_folder_button = QPushButton("Wybierz folder")
        self.rename_button = QPushButton("Zmień nazwę karty")
        self.delete_button = QPushButton("Usuń kartę")
        self.print_button = QPushButton("Drukuj")
        self.toggle_pdf_button = QPushButton("Wyświetl / Zamknij kartę")

        # IKONY SYSTEMOWE
        self.choose_folder_button.setIcon(self.sys_icon("folder", QStyle.SP_DirIcon))
        self.rename_button.setIcon(self.sys_icon("document-edit", QStyle.SP_FileDialogDetailedView))
        self.delete_button.setIcon(self.sys_icon("edit-delete", QStyle.SP_TrashIcon))
        self.print_button.setIcon(self.sys_icon("document-print", QStyle.SP_FileDialogDetailedView))
        self.toggle_pdf_button.setIcon(self.sys_icon("x-office-document", QStyle.SP_FileIcon))

        for btn in [
            self.choose_folder_button,
            self.rename_button,
            self.delete_button,
            self.print_button,
            self.toggle_pdf_button
        ]:
            btn.setIconSize(QSize(20, 20))

        # PODŁĄCZENIE FUNKCJI
        self.choose_folder_button.clicked.connect(self.choose_folder)
        self.rename_button.clicked.connect(self.rename_pdf)
        self.delete_button.clicked.connect(self.delete_pdf)
        self.print_button.clicked.connect(self.print_pdf)
        self.toggle_pdf_button.clicked.connect(self.toggle_pdf_view)

        buttons_layout.addWidget(self.choose_folder_button)
        buttons_layout.addWidget(self.rename_button)
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.print_button)
        buttons_layout.addWidget(self.toggle_pdf_button)

        # Dodanie elementów do prawego panelu
        right_panel.addWidget(self.header_widget)
        right_panel.addWidget(self.pdf_view)
        right_panel.addLayout(buttons_layout)

        # -------- ŁĄCZENIE PANELI --------
        main_layout.addLayout(left_panel, 1)
        main_layout.addLayout(right_panel, 3)

    # ================= STYLE =================
    def _apply_styles(self):
        # Nagłówek
        self.header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1e3c72,
                    stop:1 #2a5298
                );
                border-radius: 10px;
            }
        """)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 32px;
                font-weight: bold;
                letter-spacing: 2px;
            }
        """)
        self.version_label.setStyleSheet("""
            QLabel {
                color: #dcdcdc;
                font-size: 12px;
            }
        """)
        # Informacje o autorze i prawach zastrzeżonych
        self.copyright_label.setStyleSheet("""
            QLabel {
                color: #dcdcdc;
                font-size: 10px;
                font-style: italic;
            }
        """)

        # Dolne przyciski
        self.choose_folder_button.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #5a32a3; }
        """)
        self.rename_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e68900; }
        """)
        self.delete_button.setStyleSheet("""
            QPushButton {
                background-color: #d9534f;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #c9302c; }
        """)
        self.print_button.setStyleSheet("""
            QPushButton {
                background-color: #5cb85c;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #449d44; }
        """)
        self.toggle_pdf_button.setStyleSheet("""
            QPushButton {
                background-color: #0275d8;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #025aa5; }
        """)

    # ================= LOGIKA =================
    def _load_pdfs(self):
        self.pdf_index.clear()
        self.list_widget.clear()
        if not PDF_DIR.exists():
            QMessageBox.warning(self, "Błąd", f"Folder nie istnieje:\n{PDF_DIR}")
            return
        for pdf_path in PDF_DIR.rglob("*.pdf"):
            self.pdf_index.append((pdf_path, None))
            item = QListWidgetItem(pdf_path.stem)
            item.setData(1, pdf_path)
            self.list_widget.addItem(item)

    def search(self, query):
        query = query.lower().strip()
        self.list_widget.clear()
        for path, _ in self.pdf_index:
            if not query or query in path.stem.lower():
                item = QListWidgetItem(path.stem)
                item.setData(1, path)
                self.list_widget.addItem(item)

    def open_pdf_from_list(self, item):
        self.current_pdf_path = item.data(1)

    def display_pdf_from_list(self, item):
        self.current_pdf_path = item.data(1)
        self._show_pdf()

    def _show_pdf(self):
        if self.pdf_visible:
            self.close_current_pdf()
        if self.current_pdf_path.exists():
            self.pdf_document.load(str(self.current_pdf_path))
            self.pdf_view.setDocument(self.pdf_document)
            self.pdf_visible = True
        else:
            QMessageBox.warning(self, "Błąd", "Plik PDF nie istnieje!")

    def choose_folder(self):
        global PDF_DIR
        folder = QFileDialog.getExistingDirectory(self, "Wybierz folder", str(PDF_DIR))
        if folder:
            PDF_DIR = Path(folder)
            self.close_current_pdf()
            self._load_pdfs()

    def rename_pdf(self):
        if not self.current_pdf_path:
            return
        new_name, ok = QInputDialog.getText(
            self, "Zmień nazwę", "Nowa nazwa (bez .pdf):",
            text=self.current_pdf_path.stem
        )
        if ok and new_name.strip():
            # Zamknięcie PDF przed rename
            if self.pdf_visible:
                self.pdf_view.setDocument(None)
                self.pdf_document.close()
                self.pdf_visible = False
            new_path = self.current_pdf_path.with_name(new_name.strip() + ".pdf")
            try:
                self.current_pdf_path.rename(new_path)
                self.current_pdf_path = new_path
            except PermissionError as e:
                QMessageBox.warning(self, "Błąd", f"Nie można zmienić nazwy pliku:\n{e}")
                return
            self._load_pdfs()

    def delete_pdf(self):
        if not self.current_pdf_path:
            return
        reply = QMessageBox.question(
            self, "Usuń", "Czy na pewno usunąć plik?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.pdf_visible:
                self.pdf_view.setDocument(None)
                self.pdf_document.close()
                self.pdf_visible = False
            self.current_pdf_path.unlink()
            self.current_pdf_path = None
            self._load_pdfs()

    def print_pdf(self):
        if not self.current_pdf_path:
            return
        printer = QPrinter(QPrinter.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec():
            doc = fitz.open(self.current_pdf_path)
            painter = QPainter(printer)
            for i, page in enumerate(doc):
                if i > 0:
                    printer.newPage()
                painter.drawImage(0, 0, page.get_pixmap(dpi=300).toqimage())
            painter.end()

    def toggle_pdf_view(self):
        if not self.current_pdf_path:
            return
        if self.pdf_visible:
            self.close_current_pdf()
        else:
            self._show_pdf()

    def close_current_pdf(self):
        if self.pdf_visible:
            self.pdf_document.close()
            self.pdf_view.setDocument(None)
            self.pdf_visible = False


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SDSBrowser()
    window.show()
    sys.exit(app.exec())
