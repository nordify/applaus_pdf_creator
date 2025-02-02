import sys
import subprocess
import os
from tempfile import NamedTemporaryFile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QLineEdit, QComboBox, QScrollArea, QFrame, QGridLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtGui import QPixmap, QIntValidator, QIcon
from PyQt5.QtCore import Qt, QTranslator, QLibraryInfo, QLocale
from fpdf import FPDF

os.environ["LANG"] = "de_DE.UTF-8"

class DraggableLabel(QLabel):
    def __init__(self, parent, file_path, main_window):
        super().__init__(parent)
        self.file_path = file_path
        self.main_window = main_window
        self.setAcceptDrops(True)

class ImageUploader(QWidget):
    def __init__(self):
        super().__init__()
        translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        translator.load("qtwidgets_de", translations_path)
        self.setLocale(QLocale(QLocale.German, QLocale.Germany))
        self.initUI()
        self.setWindowTitle("PDF Creator")
        self.images = []
        self.temp_files = []

    def initUI(self):
        layout = QVBoxLayout()
        self.setAcceptDrops(True)
        self.setMinimumSize(750, 600)
        self.setMaximumSize(750, 600)

        self.aktennummer_input = QLineEdit(self)
        self.aktennummer_input.setPlaceholderText("Aktennummer")
        self.aktennummer_input.setValidator(QIntValidator())
        self.aktennummer_input.textChanged.connect(self.updatePdfButtonState)
        
        self.dokumentenkürzel_input = QComboBox(self)
        self.dokumentenkürzel_input.addItems(["GA", "ST", "PR"])
        
        self.dokumentenzahl_input = QLineEdit(self)
        self.dokumentenzahl_input.setPlaceholderText("Dokumentenzahl")
        self.dokumentenzahl_input.setValidator(QIntValidator())
        self.dokumentenzahl_input.textChanged.connect(self.updatePdfButtonState)

        layout.addWidget(QLabel("Aktennummer:"))
        layout.addWidget(self.aktennummer_input)
        layout.addWidget(QLabel("Dokumentenkürzel:"))
        layout.addWidget(self.dokumentenkürzel_input)
        layout.addWidget(QLabel("Dokumentenzahl:"))
        layout.addWidget(self.dokumentenzahl_input)

        self.upload_button = QPushButton("Dateien hinzufügen", self)
        self.upload_button.clicked.connect(self.openFileDialog)
        layout.addWidget(self.upload_button)
        
        self.image_area = QScrollArea()
        self.image_container = QWidget()
        self.image_layout = QGridLayout()
        self.image_layout.setAlignment(Qt.AlignTop)
        self.image_container.setLayout(self.image_layout)
        self.image_area.setWidget(self.image_container)
        self.image_area.setWidgetResizable(True)
        layout.addWidget(self.image_area)

        self.empty_label = QLabel("Importiere Fotos oder ziehe sie hierhin", self.image_container)
        self.empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self.empty_label.setAlignment(Qt.AlignCenter)
        self.empty_layout = QVBoxLayout()
        self.empty_layout.addStretch()
        self.empty_layout.addWidget(self.empty_label)
        self.empty_layout.addStretch()
        self.image_layout.addLayout(self.empty_layout, 0, 0)

        self.orientation_input = QComboBox(self)
        self.orientation_input.addItems(["Hochformat", "Querformat"])
        layout.addWidget(QLabel("Bildformat:"))
        layout.addWidget(self.orientation_input)
        
        pdf_buttons_layout = QHBoxLayout()
        
        self.pdf_button = QPushButton("PDF erstellen", self)
        self.pdf_button.setEnabled(False)
        self.pdf_button.clicked.connect(self.createPDF)
        pdf_buttons_layout.addWidget(self.pdf_button)
        
        self.reset_button = QPushButton("Zurücksetzen", self)
        self.reset_button.setStyleSheet("color: #ff453a;")
        self.reset_button.clicked.connect(self.resetApp)
        pdf_buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(pdf_buttons_layout)
        
        self.setLayout(layout)

        self.overlay = QLabel(self)
        self.overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.3);")
        self.overlay.setAlignment(Qt.AlignCenter)
        self.overlay.setText("Drag & Drop Here")
        self.overlay.setVisible(False)

    def rearrangeImages(self):
        for i in reversed(range(self.image_layout.count())):
            item = self.image_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and not isinstance(widget, QVBoxLayout):
                    self.image_layout.removeWidget(widget)
                    widget.setParent(None)
        for idx, (frame, _) in enumerate(self.images):
            row = idx // 4
            col = idx % 4
            self.image_layout.addWidget(frame, row, col)
        self.empty_label.setVisible(len(self.images) == 0)

    def resizeEvent(self, event):
        self.overlay.setGeometry(self.rect())

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.overlay.setVisible(True)

    def dragLeaveEvent(self, event):
        self.overlay.setVisible(False)

    def dropEvent(self, event):
        self.overlay.setVisible(False)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    self.addImage(file_path)

    def openFileDialog(self):
        options = QFileDialog.Options()
        dialog = QFileDialog()
        files, _ = dialog.getOpenFileNames(
            self, 
            "Bilder auswählen", 
            "", 
            "Bilder (*.png *.jpg *.jpeg *.bmp);;Alle Dateien (*)", 
            options=options
        )
        if files:
            for file in files:
                self.addImage(file)

    def addImage(self, file_path):
        frame = QFrame(self.image_container)
        container = QWidget(frame)
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        pixmap = QPixmap(file_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        label = DraggableLabel(container, file_path, self)
        label.setPixmap(pixmap)
        label.setAlignment(Qt.AlignCenter)

        remove_button = QPushButton("✖", container)
        remove_button.setFixedSize(16, 16)
        remove_button.clicked.connect(lambda: self.removeImage(frame, file_path))
        remove_button.setStyleSheet("""
            QPushButton {
                background-color: rgb(102, 102, 102);
                color: white;
                border-radius: 8px;
                font-size: 11px;
                border: none;
            }
            QPushButton:hover {
                background-color: rgb(150, 150, 150);
            }
        """)

        layout.addWidget(label, 0, 0, Qt.AlignCenter)
        layout.addWidget(remove_button, 0, 0, Qt.AlignTop | Qt.AlignRight)
        
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(container)

        self.images.append((frame, file_path))
        self.rearrangeImages()
        self.updatePdfButtonState()

    def removeImage(self, frame, file_path):
        self.image_layout.removeWidget(frame)
        frame.deleteLater()
        self.images = [img for img in self.images if img[1] != file_path]
        self.rearrangeImages()
        self.updatePdfButtonState()

    def resetApp(self):
        self.aktennummer_input.clear()
        self.dokumentenkürzel_input.setCurrentIndex(0)
        self.dokumentenzahl_input.clear()
        self.orientation_input.setCurrentIndex(0)
        for frame, _ in self.images:
            self.image_layout.removeWidget(frame)
            frame.deleteLater()
        self.images.clear()
        self.empty_label.setVisible(True)
        self.updatePdfButtonState()

    def updatePdfButtonState(self):
        aktennummer_filled = bool(self.aktennummer_input.text().strip())
        dokumentenzahl_filled = bool(self.dokumentenzahl_input.text().strip())
        images_present = bool(self.images)
        self.pdf_button.setEnabled(aktennummer_filled and dokumentenzahl_filled and images_present)

    def processImage(self, file_path):
        pixmap = QPixmap(file_path)
        if pixmap.isNull():
            return file_path
        width = pixmap.width()
        height = pixmap.height()
        max_side = max(width, height)
        if max_side > 2000:
            scale_factor = 2000 / max_side
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            pixmap = pixmap.scaled(new_width, new_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        temp = NamedTemporaryFile(delete=False, suffix=".jpg")
        temp_path = temp.name
        pixmap.save(temp_path, "JPEG", quality=85)
        self.temp_files.append(temp_path)
        return temp_path

    def createPDF(self):
        if not self.images:
            QMessageBox.warning(self, "Keine Bilder", "Bitte fügen Sie mindestens ein Bild hinzu.")
            return

        aktennummer = self.aktennummer_input.text()
        dokumentenkürzel = self.dokumentenkürzel_input.currentText()
        dokumentenzahl = self.dokumentenzahl_input.text()
        if not aktennummer or not dokumentenzahl:
            QMessageBox.warning(self, "Fehlende Eingaben", "Bitte füllen Sie alle Eingabefelder aus.")
            return

        options = QFileDialog.Options()
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "PDF speichern",
            f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl}_Fotos.pdf",
            "PDF Files (*.pdf);;All Files (*)",
            options=options
        )
        if not save_path:
            return

        try:
            orientation = self.orientation_input.currentText()
            pdf_orientation = "L" if orientation == "Hochformat" else "P"
            pdf = FPDF(orientation=pdf_orientation, unit="mm", format="A4")
            margin = 10
            spacing = 10
            images_per_page = 2
            text_space = 10
            buffer = 15

            if pdf_orientation == "L":
                page_width = 297
                page_height = 210
            else:
                page_width = 210
                page_height = 297

            if pdf_orientation == "P":
                img_max_height = (page_height - 2 * margin - (images_per_page - 1) * spacing - images_per_page * text_space - buffer) / images_per_page
                img_max_width = page_width - 2 * margin
            else:
                img_max_width = (page_width - 2 * margin - (images_per_page - 1) * spacing) / images_per_page
                img_max_height = page_height - 2 * margin - text_space - 20

            for i in range(0, len(self.images), images_per_page):
                pdf.add_page()
                list_of_images_in_page = self.images[i:i+images_per_page]

                if pdf_orientation == "P":
                    for j, (frame, file_path) in enumerate(list_of_images_in_page):
                        processed_path = self.processImage(file_path)
                        img = QPixmap(processed_path)
                        img_width = img.width()
                        img_height = img.height()
                        aspect_ratio = img_width / img_height

                        if aspect_ratio > (img_max_width / img_max_height):
                            display_width = img_max_width
                            display_height = img_max_width / aspect_ratio
                        else:
                            display_height = img_max_height
                            display_width = img_max_height * aspect_ratio

                        x_pos = margin + (img_max_width - display_width) / 2
                        y_pos = margin + j * (img_max_height + spacing + text_space)
                        pdf.image(processed_path, x=x_pos, y=y_pos, w=display_width, h=display_height)

                        ext = os.path.splitext(file_path)[1][1:].lower()
                        image_number = i + j + 1
                        text = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {image_number}.{ext}"

                        pdf.set_font("Arial", "B", 12)
                        text_width = pdf.get_string_width(text)
                        text_x = x_pos + (display_width - text_width) / 2
                        text_y = y_pos + display_height + 2
                        if text_y + 10 > page_height - margin:
                            text_y = page_height - margin - 10

                        pdf.set_xy(text_x, text_y)
                        pdf.cell(text_width, 10, text)
                else:
                    max_display_height = 0
                    display_dimensions = []
                    processed_paths = []
                    for j, (frame, file_path) in enumerate(list_of_images_in_page):
                        processed_path = self.processImage(file_path)
                        processed_paths.append(processed_path)
                        img = QPixmap(processed_path)
                        img_width = img.width()
                        img_height = img.height()
                        aspect_ratio = img_width / img_height

                        if aspect_ratio > (img_max_width / img_max_height):
                            display_width = img_max_width
                            display_height = img_max_width / aspect_ratio
                        else:
                            display_height = img_max_height
                            display_width = img_max_height * aspect_ratio

                        display_dimensions.append((display_width, display_height))
                        if display_height > max_display_height:
                            max_display_height = display_height

                    y_pos = margin + (img_max_height - max_display_height) / 2

                    for j, (frame, file_path) in enumerate(list_of_images_in_page):
                        display_width, display_height = display_dimensions[j]
                        cell_x = margin + j * (img_max_width + spacing)
                        x_pos = cell_x + (img_max_width - display_width) / 2
                        pdf.image(processed_paths[j], x=x_pos, y=y_pos, w=display_width, h=display_height)

                    text_y = y_pos + max_display_height + 2

                    for j, (frame, file_path) in enumerate(list_of_images_in_page):
                        ext = os.path.splitext(file_path)[1][1:].lower()
                        image_number = i + j + 1
                        text = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {image_number}.{ext}"
                        pdf.set_font("Arial", "B", 12)
                        text_width = pdf.get_string_width(text)
                        cell_x = margin + j * (img_max_width + spacing)
                        text_x = cell_x + (img_max_width - text_width) / 2
                        pdf.set_xy(text_x, text_y)
                        pdf.cell(text_width, 10, text)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Beim Erstellen der PDF ist ein Fehler aufgetreten:\n{str(e)}")
        else:
            pdf.output(save_path)
            QMessageBox.information(self, "PDF erstellt", f"PDF erfolgreich erstellt:\n{save_path}")
            if sys.platform == "win32":
                os.startfile(save_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", save_path])
            else:
                subprocess.run(["xdg-open", save_path])
        finally:
            for temp_path in self.temp_files:
                try:
                    os.remove(temp_path)
                except Exception as e:
                    print(f"Temporäre Datei konnte nicht gelöscht werden: {temp_path}. Fehler: {e}")
            self.temp_files.clear()

if __name__ == '__main__':    
    app = QApplication(sys.argv)
    translator = QTranslator()
    translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator.load("qtwidgets_de", translations_path)
    app.installTranslator(translator)
    app.setWindowIcon(QIcon("icon.png"))
    ex = ImageUploader()
    ex.show()
    sys.exit(app.exec_())