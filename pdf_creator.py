import sys
import subprocess
import os
from tempfile import NamedTemporaryFile
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QLineEdit, QComboBox, QScrollArea, QFrame, QGridLayout, QHBoxLayout, QMessageBox, QSizePolicy, QProgressDialog
)
from PyQt5.QtGui import QPixmap, QIntValidator, QImage
from PyQt5.QtCore import Qt, QTranslator, QLibraryInfo, QLocale
from fpdf import FPDF
from PIL import Image, ImageOps
from io import BytesIO

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
        self.aktennummer_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.aktennummer_input.setPlaceholderText("Aktennummer")
        self.aktennummer_input.setValidator(QIntValidator())
        self.aktennummer_input.textChanged.connect(self.updatePdfButtonState)
        
        self.dokumentenkürzel_input = QComboBox(self)
        self.dokumentenkürzel_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.dokumentenkürzel_input.setContentsMargins(0, 0, 0, 0)
        self.dokumentenkürzel_input.addItems(["GA", "ST", "PR", "UB"])
        
        self.dokumentenzahl_input = QLineEdit(self)
        self.dokumentenzahl_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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
        
        pdf_buttons_layout = QHBoxLayout()   
        pdf_buttons_layout.setContentsMargins(150, 10, 150, 0)
        pdf_buttons_layout.setSpacing(10)
        
        self.pdf_button = QPushButton("PDF erstellen", self)
        self.pdf_button.setEnabled(False)
        self.pdf_button.clicked.connect(self.createPDF)
        self.pdf_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        pdf_buttons_layout.addWidget(self.pdf_button)
        
        self.reset_button = QPushButton("Zurücksetzen", self)
        self.reset_button.setStyleSheet("color: #ff453a;")
        self.reset_button.clicked.connect(self.resetApp)
        self.reset_button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

    def showProgress(self, max, text):
        progress_dialog = QProgressDialog(text, "Cancel", 0, max, self)
        progress_dialog.setWindowModality(Qt.WindowModal)
        progress_dialog.setMinimumDuration(0)
        progress_dialog.show()
        return progress_dialog

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except AttributeError:
            base_path = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base_path, relative_path)

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
            valid_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                    valid_files.append(file_path)
            
            progress_dialog = self.showProgress(len(valid_files), "Importing images...")

            for i, file_path in enumerate(valid_files):
                if progress_dialog.wasCanceled():
                    break
                self.addImage(file_path)
                progress_dialog.setValue(i + 1)
                QApplication.processEvents()


    def openFileDialog(self):
        homedir = os.environ['HOME']
        options = QFileDialog.Options()
        dialog = QFileDialog()
        files, _ = dialog.getOpenFileNames(
            parent=self, 
            caption="Bilder auswählen", 
            directory=homedir, 
            filter="Bilder (*.png *.jpg *.jpeg *.bmp);;Alle Dateien (*)", 
            options=options
        )
        if files:
            progress_dialog = self.showProgress(len(files), "Importing images...")

            for i, file in enumerate(files):
                if progress_dialog.wasCanceled():
                    break
                try:
                    self.addImage(file)
                except Exception as err:
                    print(f"Fehler: {err}")
                progress_dialog.setValue(i + 1)
                QApplication.processEvents()


    def fix_orientation_with_pillow(self, file_path):
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            
            buf = BytesIO()
            img.save(buf, format='JPEG')
            
            qimage = QImage.fromData(buf.getvalue())
            return QPixmap.fromImage(qimage)


    def addImage(self, file_path):
        frame = QFrame(self.image_container)
        container = QWidget(frame)
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        pixmap_original = self.fix_orientation_with_pillow(file_path)

        pixmap = pixmap_original.scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
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
        reply = QMessageBox.question(self, 'Bestätigung', 'Möchten Sie die App wirklich zurücksetzen?',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.aktennummer_input.clear()
            self.dokumentenkürzel_input.setCurrentIndex(0)
            self.dokumentenzahl_input.clear()
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
        try:
            from PIL import Image, ImageOps
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img)
                max_side = max(img.width, img.height)
                if max_side > 2000:
                    scale_factor = 2000 / max_side
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img = img.resize((new_width, new_height), Image.LANCZOS)

                temp = NamedTemporaryFile(delete=False, suffix=".jpg")
                img.save(temp, format="JPEG", quality=85)
                temp_path = temp.name
                self.temp_files.append(temp_path)
                return temp_path
        except Exception as e:
            print("Fehler beim Lesen/Transponieren:", e)
            return file_path
    
    def is_horizontal(self, file_path):
        with Image.open(file_path) as img:
            img = ImageOps.exif_transpose(img)
            width, height = img.size
        return width >= height

    def group_images(self, images):
        grouped = []
        i = 0
        n = len(images)
        
        while i < n:
            current_frame, current_path = images[i]
            if not self.is_horizontal(current_path):
                grouped.append([images[i]])
                i += 1
            else:
                if i + 1 < n:
                    next_frame, next_path = images[i + 1]
                    if self.is_horizontal(next_path):
                        grouped.append([images[i], images[i + 1]])
                        i += 2
                        continue
                grouped.append([images[i]])
                i += 1

        return grouped
    
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

        try:
            options = QFileDialog.Options()
            first_image_dir = os.path.dirname(self.images[0][1])
            save_path, _ = QFileDialog.getSaveFileName(
                self,
                "PDF speichern",
                f"{first_image_dir}/{aktennummer}-{dokumentenkürzel}-{dokumentenzahl}_Fotos.pdf",
                "PDF Files (*.pdf);;All Files (*)",
                options=options
            )
            if not save_path:
                return

            progress_pdf = self.showProgress(1, "Creating PDF...")
            QApplication.processEvents()

            grouped_images = self.group_images(self.images)
            total_images = sum(len(group) for group in grouped_images)
            progress_pdf.setMaximum(total_images)
            progress_value = 0

            pdf = FPDF(orientation="P", unit="mm", format="A4")
            page_width = 210
            page_height = 297

            margin_top_bottom = 10

            briefkopf_path = self.resource_path(os.path.join('resources', 'briefkopf.png'))
            briefkopf_width_in_pdf = page_width / 3
            briefkopf_img = QPixmap(briefkopf_path)
            aspect_briefkopf = briefkopf_img.width() / briefkopf_img.height()
            briefkopf_height_in_pdf = briefkopf_width_in_pdf / aspect_briefkopf

            content_top = margin_top_bottom + briefkopf_height_in_pdf
            content_height = page_height - margin_top_bottom - content_top

            text_line_height = 10
            spacing_between = 10

            uniform_img_dim = (content_height - spacing_between - 2 * text_line_height) / 2

            global_image_counter = 1

            for page_idx, group in enumerate(grouped_images):
                if progress_pdf.wasCanceled():
                    break

                pdf.add_page()

                x_briefkopf = (page_width - briefkopf_width_in_pdf) / 2
                y_briefkopf = margin_top_bottom
                pdf.image(
                    briefkopf_path,
                    x=x_briefkopf,
                    y=y_briefkopf,
                    w=briefkopf_width_in_pdf,
                    h=briefkopf_height_in_pdf
                )

                if len(group) == 1:
                    label, file_path = group[0]
                    processed_path = self.processImage(file_path)
                    img = QPixmap(processed_path)
                    orig_w, orig_h = img.width(), img.height()

                    new_width = uniform_img_dim
                    new_height = orig_h * (new_width / orig_w)

                    block_total_height = new_height + text_line_height
                    y_block_top = content_top + (content_height - block_total_height) / 2
                    x_image = (page_width - new_width) / 2
                    y_image = y_block_top

                    pdf.image(processed_path, x=x_image, y=y_image, w=new_width, h=new_height)

                    pdf.set_font("Arial", "B", 14)
                    text = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {global_image_counter}"
                    text_width = pdf.get_string_width(text)
                    x_text = (page_width - text_width) / 2
                    y_text = y_image + new_height + 4
                    pdf.set_xy(x_text, y_text)
                    pdf.cell(text_width, text_line_height, text, align="C")

                    global_image_counter += 1
                    progress_value += 1
                    progress_pdf.setValue(progress_value)

                elif len(group) == 2:
                    (label1, file_path1), (label2, file_path2) = group
                    processed_path1 = self.processImage(file_path1)
                    processed_path2 = self.processImage(file_path2)

                    img1 = QPixmap(processed_path1)
                    img2 = QPixmap(processed_path2)
                    orig1_w, orig1_h = img1.width(), img1.height()
                    orig2_w, orig2_h = img2.width(), img2.height()

                    pdf.set_font("Arial", "B", 14)
                    text1 = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {global_image_counter}"
                    text2 = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl} Foto Nr. {global_image_counter + 1}"
                    text1_width = pdf.get_string_width(text1)
                    text2_width = pdf.get_string_width(text2)

                    new1_width = uniform_img_dim
                    new1_height = orig1_h * (new1_width / orig1_w)
                    new2_width = uniform_img_dim
                    new2_height = orig2_h * (new2_width / orig2_w)

                    block_total_height = (new1_height + text_line_height) + spacing_between + (new2_height + text_line_height)
                    y_block_top = content_top + (content_height - block_total_height) / 2

                    x1 = (page_width - new1_width) / 2
                    y1 = y_block_top
                    pdf.image(processed_path1, x=x1, y=y1, w=new1_width, h=new1_height)

                    x_text1 = (page_width - text1_width) / 2
                    y_text1 = y1 + new1_height + 4
                    pdf.set_xy(x_text1, y_text1)
                    pdf.cell(text1_width, text_line_height, text1, align="C")

                    y2 = y_text1 + text_line_height + spacing_between
                    x2 = (page_width - new2_width) / 2
                    pdf.image(processed_path2, x=x2, y=y2, w=new2_width, h=new2_height)

                    x_text2 = (page_width - text2_width) / 2
                    y_text2 = y2 + new2_height + 4
                    pdf.set_xy(x_text2, y_text2)
                    pdf.cell(text2_width, text_line_height, text2, align="C")

                    global_image_counter += 2
                    progress_value += 2
                    progress_pdf.setValue(progress_value)

                QApplication.processEvents()

            progress_pdf.close()
            pdf.output(save_path)

            QMessageBox.information(self, "PDF erstellt", f"PDF erfolgreich erstellt:\n{save_path}")
            if sys.platform == "win32":
                os.startfile(save_path)
            elif sys.platform == "darwin":
                subprocess.run(["open", save_path])
            else:
                subprocess.run(["xdg-open", save_path])

        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Beim Erstellen der PDF ist ein Fehler aufgetreten:\n{str(e)}")
        finally:
            for temp_path in getattr(self, 'temp_files', []):
                try:
                    os.remove(temp_path)
                except Exception as err:
                    print(f"Temporäre Datei konnte nicht gelöscht werden: {temp_path}. Fehler: {err}")
            self.temp_files.clear()


if __name__ == '__main__':    
    app = QApplication(sys.argv)
    translator = QTranslator()
    translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
    translator.load("qtbase_de", translations_path)
    app.installTranslator(translator)
    ex = ImageUploader()
    ex.show()
    sys.exit(app.exec_())