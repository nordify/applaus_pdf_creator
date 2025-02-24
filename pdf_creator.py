import sys
import os
import subprocess
import shutil
from io import BytesIO
from PIL import Image, ImageOps
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QLineEdit, QComboBox, QScrollArea, QFrame, QGridLayout, QHBoxLayout, QMessageBox,
    QSizePolicy, QProgressDialog
)
from PyQt6.QtGui import QPixmap, QIntValidator, QImage, QIcon
from PyQt6.QtCore import Qt, QTranslator, QLibraryInfo, QLocale, QThread, pyqtSignal
from fpdf import FPDF

os.environ["LANG"] = "de_DE.UTF-8"

class ImageImportWorker(QThread):
    imageImported = pyqtSignal(str, QImage)
    progress = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, file_paths):
        super().__init__()
        self.file_paths = file_paths
        self._isCanceled = False

    def cancel(self):
        self._isCanceled = True

    def run(self):
        count = 0
        for file_path in self.file_paths:
            if self._isCanceled:
                break
            try:
                with Image.open(file_path) as img:
                    img = ImageOps.exif_transpose(img)
                    if img.mode in ("RGBA", "LA"):
                        img = img.convert("RGB")
                    buf = BytesIO()
                    img.save(buf, format='JPEG')
                    qimg = QImage.fromData(buf.getvalue())
                self.imageImported.emit(file_path, qimg)
            except Exception as err:
                print(f"Fehler beim Importieren {file_path}: {err}")
            count += 1
            self.progress.emit(count)
        self.finished.emit()

class PDFCreationWorker(QThread):
    progressUpdate = pyqtSignal(int)
    finished = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)

    def __init__(self, image_paths, aktennummer, dokumentenkürzel, dokumentenzahl, pdf_path, briefkopf_path, output_folder):
        super().__init__()
        self.image_paths = image_paths
        self.aktennummer = aktennummer
        self.dokumentenkürzel = dokumentenkürzel
        self.dokumentenzahl = dokumentenzahl
        self.save_path = pdf_path
        self.briefkopf_path = briefkopf_path
        self.output_folder = output_folder
        self._isCanceled = False

    def cancel(self):
        self._isCanceled = True

    def is_horizontal(self, file_path):
        try:
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img)
                width, height = img.size
            return width >= height
        except Exception as e:
            print("Error in is_horizontal:", e)
            return False

    def processImage(self, file_path, image_counter):
        try:
            with Image.open(file_path) as img:
                img = ImageOps.exif_transpose(img)
                if img.mode in ("RGBA", "LA"):
                    img = img.convert("RGB")
                max_side = max(img.width, img.height)
                if max_side > 2000:
                    scale_factor = 2000 / max_side
                    new_width = int(img.width * scale_factor)
                    new_height = int(img.height * scale_factor)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                image_filename = f"{self.aktennummer}-{self.dokumentenkürzel}-{self.dokumentenzahl} Foto Nr. {image_counter}.jpg"
                final_path = os.path.join(self.output_folder, image_filename)
                img.save(final_path, format="JPEG", quality=85)
                return final_path
        except Exception as e:
            print("Fehler beim processImage:", e)
            return file_path

    def run(self):
        try:
            pdf = FPDF(orientation="P", unit="mm", format="A4")
            pdf.set_auto_page_break(False)
            page_width = 210
            page_height = 297
            margin_top_bottom = 10
            header_spacing = 10
            offset = 3
            spacing_between = 8
            text_line_height = 10
            with Image.open(self.briefkopf_path) as briefkopf_img:
                aspect_briefkopf = briefkopf_img.width / briefkopf_img.height
            briefkopf_width_in_pdf = page_width / 3
            briefkopf_height_in_pdf = briefkopf_width_in_pdf / aspect_briefkopf
            content_top = margin_top_bottom + briefkopf_height_in_pdf + header_spacing
            content_height = page_height - margin_top_bottom - content_top
            uniform_img_dim = (content_height - spacing_between) / 2 - (offset + text_line_height)
            grouped = []
            i = 0
            n = len(self.image_paths)
            while i < n:
                if not self.is_horizontal(self.image_paths[i]):
                    grouped.append([self.image_paths[i]])
                    i += 1
                else:
                    if i + 1 < n and self.is_horizontal(self.image_paths[i + 1]):
                        grouped.append([self.image_paths[i], self.image_paths[i + 1]])
                        i += 2
                    else:
                        grouped.append([self.image_paths[i]])
                        i += 1
            progress_count = 0
            global_image_counter = 1
            for group in grouped:
                if self._isCanceled:
                    break
                pdf.add_page()
                x_briefkopf = (page_width - briefkopf_width_in_pdf) / 2
                y_briefkopf = margin_top_bottom
                pdf.image(self.briefkopf_path, x=x_briefkopf, y=y_briefkopf, w=briefkopf_width_in_pdf, h=briefkopf_height_in_pdf)
                if len(group) == 1:
                    file_path = group[0]
                    processed_path = self.processImage(file_path, global_image_counter)
                    with Image.open(processed_path) as img:
                        orig_w, orig_h = img.size
                    new_width = uniform_img_dim
                    new_height = orig_h * (new_width / orig_w)
                    block_total_height = new_height + offset + text_line_height
                    y_block_top = content_top + (content_height - block_total_height) / 2
                    x_image = (page_width - new_width) / 2
                    y_image = y_block_top
                    pdf.image(processed_path, x=x_image, y=y_image, w=new_width, h=new_height)
                    pdf.set_font("Arial", "B", 11)
                    text = f"{self.aktennummer}-{self.dokumentenkürzel}-{self.dokumentenzahl} Foto Nr. {global_image_counter}"
                    text_width = pdf.get_string_width(text)
                    x_text = (page_width - text_width) / 2
                    y_text = y_image + new_height + offset
                    pdf.set_xy(x_text, y_text)
                    pdf.cell(text_width, text_line_height, text, align="C")
                    global_image_counter += 1
                    progress_count += 1
                    self.progressUpdate.emit(progress_count)
                elif len(group) == 2:
                    file_path1, file_path2 = group
                    processed_path1 = self.processImage(file_path1, global_image_counter)
                    processed_path2 = self.processImage(file_path2, global_image_counter + 1)
                    with Image.open(processed_path1) as img1:
                        orig1_w, orig1_h = img1.size
                    with Image.open(processed_path2) as img2:
                        orig2_w, orig2_h = img2.size
                    pdf.set_font("Arial", "B", 11)
                    text1 = f"{self.aktennummer}-{self.dokumentenkürzel}-{self.dokumentenzahl} Foto Nr. {global_image_counter}"
                    text2 = f"{self.aktennummer}-{self.dokumentenkürzel}-{self.dokumentenzahl} Foto Nr. {global_image_counter + 1}"
                    text1_width = pdf.get_string_width(text1)
                    text2_width = pdf.get_string_width(text2)
                    new1_width = uniform_img_dim
                    new1_height = orig1_h * (new1_width / orig1_w)
                    new2_width = uniform_img_dim
                    new2_height = orig2_h * (new2_width / orig2_w)
                    block_total_height = (new1_height + offset + text_line_height) + spacing_between + (new2_height + offset + text_line_height)
                    y_block_top = content_top + (content_height - block_total_height) / 2
                    x1 = (page_width - new1_width) / 2
                    y1 = y_block_top
                    pdf.image(processed_path1, x=x1, y=y1, w=new1_width, h=new1_height)
                    x_text1 = (page_width - text1_width) / 2
                    y_text1 = y1 + new1_height + offset
                    pdf.set_xy(x_text1, y_text1)
                    pdf.cell(text1_width, text_line_height, text1, align="C")
                    y2 = y_text1 + text_line_height + spacing_between
                    x2 = (page_width - new2_width) / 2
                    pdf.image(processed_path2, x=x2, y=y2, w=new2_width, h=new2_height)
                    x_text2 = (page_width - text2_width) / 2
                    y_text2 = y2 + new2_height + offset
                    pdf.set_xy(x_text2, y_text2)
                    pdf.cell(text2_width, text_line_height, text2, align="C")
                    global_image_counter += 2
                    progress_count += 2
                    self.progressUpdate.emit(progress_count)
            if not self._isCanceled:
                pdf.output(self.save_path)
            self.finished.emit(self.save_path)
        except Exception as e:
            self.errorOccurred.emit(str(e))

class DraggableLabel(QLabel):
    def __init__(self, parent, file_path, main_window):
        super().__init__(parent)
        self.file_path = file_path
        self.main_window = main_window
        self.setAcceptDrops(True)

class ImageUploader(QWidget):
    def __init__(self):
        super().__init__()
        translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        translator = QTranslator()
        translator.load("qtwidgets_de", translations_path)
        self.setLocale(QLocale(QLocale.Language.German))
        self.initUI()
        self.setWindowTitle("PDF Creator")
        self.images = []
        self.import_worker = None
        self.pdf_worker = None

    def initUI(self):
        layout = QVBoxLayout()
        self.setAcceptDrops(True)
        self.setMinimumSize(750, 600)
        self.setMaximumSize(750, 600)
        self.aktennummer_input = QLineEdit(self)
        self.aktennummer_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.aktennummer_input.setPlaceholderText("Aktennummer")
        self.aktennummer_input.setValidator(QIntValidator())
        self.aktennummer_input.textChanged.connect(self.updatePdfButtonState)
        self.dokumentenkürzel_input = QComboBox(self)
        self.dokumentenkürzel_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.dokumentenkürzel_input.addItems(["GA", "ST", "PR", "UB", "OT", "BWS"])
        self.dokumentenzahl_input = QLineEdit(self)
        self.dokumentenzahl_input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
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
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.image_container.setLayout(self.image_layout)
        self.image_area.setWidget(self.image_container)
        self.image_area.setWidgetResizable(True)
        layout.addWidget(self.image_area)
        self.empty_label = QLabel("Importiere Fotos oder ziehe sie hierhin", self.image_container)
        self.empty_label.setStyleSheet("color: rgba(255, 255, 255, 0.5);")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        self.pdf_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pdf_buttons_layout.addWidget(self.pdf_button)
        self.reset_button = QPushButton("Zurücksetzen", self)
        self.reset_button.setStyleSheet("color: #ff453a;")
        self.reset_button.clicked.connect(self.resetApp)
        self.reset_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        pdf_buttons_layout.addWidget(self.reset_button)
        layout.addLayout(pdf_buttons_layout)
        self.setLayout(layout)
        self.overlay = QLabel(self)
        self.overlay.setStyleSheet("background-color: rgba(255, 255, 255, 0.3);")
        self.overlay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.overlay.setText("Drag & Drop Here")
        self.overlay.setVisible(False)

    def rearrangeImages(self):
        for i in reversed(range(self.image_layout.count())):
            item = self.image_layout.itemAt(i)
            if item:
                widget = item.widget()
                if widget and widget != self.empty_label:
                    self.image_layout.removeWidget(widget)
                    widget.setParent(None)
        for idx, (frame, _) in enumerate(self.images):
            row = idx // 4
            col = idx % 4
            self.image_layout.addWidget(frame, row, col)
        self.empty_label.setVisible(len(self.images) == 0)

    def showProgress(self, maximum, text):
        progress_dialog = QProgressDialog(text, "Cancel", 0, maximum, self)
        progress_dialog.setWindowModality(Qt.WindowModality.WindowModal)
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
            self.raise_()
            self.activateWindow()

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
            if valid_files:
                self.startImageImport(valid_files)

    def openFileDialog(self):
        homedir = os.environ.get('HOME', '')
        dialog = QFileDialog()
        files, _ = dialog.getOpenFileNames(
            parent=self,
            caption="Bilder auswählen",
            directory=homedir,
            filter="Bilder (*.png *.jpg *.jpeg *.bmp);;Alle Dateien (*)"
        )
        if files:
            self.startImageImport(files)

    def startImageImport(self, file_paths):
        self.import_progress_dialog = self.showProgress(len(file_paths), "Importing images...")
        self.import_worker = ImageImportWorker(file_paths)
        self.import_worker.imageImported.connect(self.addImageFromWorker)
        self.import_worker.progress.connect(lambda val: self.import_progress_dialog.setValue(val))
        self.import_progress_dialog.canceled.connect(self.import_worker.cancel)
        self.import_worker.finished.connect(self.importFinished)
        self.import_worker.start()

    def addImageFromWorker(self, file_path, qimage):
        pixmap = QPixmap.fromImage(qimage)
        frame = QFrame(self.image_container)
        container = QWidget(frame)
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        label = DraggableLabel(container, file_path, self)
        scaled_pixmap = pixmap.scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        label.setPixmap(scaled_pixmap)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
        layout.addWidget(label, 0, 0, Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(remove_button, 0, 0, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.addWidget(container)
        self.images.append((frame, file_path))
        self.rearrangeImages()
        self.updatePdfButtonState()

    def importFinished(self):
        self.import_progress_dialog.close()

    def removeImage(self, frame, file_path):
        self.image_layout.removeWidget(frame)
        frame.deleteLater()
        self.images = [img for img in self.images if img[1] != file_path]
        self.rearrangeImages()
        self.updatePdfButtonState()

    def resetApp(self):
        reply = QMessageBox.question(
            self,
            'Bestätigung',
            'Möchten Sie die App wirklich zurücksetzen?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
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

    def createPDF(self):
        if not self.images:
            QMessageBox.warning(self, "Keine Bilder", "Bitte fügen Sie mindestens ein Bild hinzu.")
            return
        aktennummer = self.aktennummer_input.text().strip()
        dokumentenkürzel = self.dokumentenkürzel_input.currentText().strip()
        dokumentenzahl = self.dokumentenzahl_input.text().strip()
        if not aktennummer or not dokumentenzahl:
            QMessageBox.warning(self, "Fehlende Eingaben", "Bitte füllen Sie alle Eingabefelder aus.")
            return
        default_folder_name = f"{aktennummer}-{dokumentenkürzel}-{dokumentenzahl}"
        first_image_dir = os.path.dirname(self.images[0][1]) if self.images else ""
        if not first_image_dir:
            first_image_dir = os.path.expanduser("~")
        folder_suggestion = os.path.join(first_image_dir, default_folder_name)
        old_folder_existed = False
        temp_renamed_folder = ""
        if os.path.isdir(folder_suggestion):
            old_folder_existed = True
            temp_renamed_folder = folder_suggestion + "_temp"
            try:
                os.rename(folder_suggestion, temp_renamed_folder)
            except Exception as e:
                QMessageBox.critical(self, "Fehler", f"Konnte Ordner nicht umbenennen:\n{e}")
                return
        folder_path, _ = QFileDialog.getSaveFileName(
            self,
            "Zielordner wählen (einfach Ordnername eingeben)",
            folder_suggestion,
            "Ordner (*)"
        )
        if not folder_path:
            if old_folder_existed and temp_renamed_folder and os.path.isdir(temp_renamed_folder):
                try:
                    os.rename(temp_renamed_folder, folder_suggestion)
                except:
                    pass
            return
        base_name = os.path.basename(folder_path)
        if base_name.lower().endswith(".pdf"):
            base_name = os.path.splitext(base_name)[0]
        parent_dir = os.path.dirname(folder_path)
        if not parent_dir:
            parent_dir = first_image_dir
        output_folder = os.path.join(parent_dir, base_name)
        if old_folder_existed:
            if output_folder == folder_suggestion:
                reply = QMessageBox.question(
                    self,
                    "Ordner existiert bereits",
                    f"Der Ordner\n\n{output_folder}\n\nexistiert bereits.\nMöchten Sie den Inhalt überschreiben?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    try:
                        shutil.rmtree(temp_renamed_folder)
                    except Exception as ex:
                        QMessageBox.critical(self, "Fehler", f"Konnte Ordner nicht löschen:\n{ex}")
                        try:
                            os.rename(temp_renamed_folder, folder_suggestion)
                        except:
                            pass
                        return
                else:
                    try:
                        os.rename(temp_renamed_folder, folder_suggestion)
                    except:
                        pass
                    return
            else:
                try:
                    os.rename(temp_renamed_folder, folder_suggestion)
                except:
                    pass
        if os.path.isdir(output_folder):
            reply = QMessageBox.question(
                self,
                "Ordner existiert bereits",
                f"Der Ordner\n\n{output_folder}\n\nexistiert bereits.\nMöchten Sie den Inhalt überschreiben?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return
            else:
                try:
                    shutil.rmtree(output_folder)
                except Exception as ex:
                    QMessageBox.critical(self, "Fehler", f"Konnte Ordner nicht löschen:\n{ex}")
                    return
        os.makedirs(output_folder, exist_ok=True)
        pdf_path = os.path.join(output_folder, f"{base_name}.pdf")
        image_paths = [p for _, p in self.images]
        def is_horizontal(fp):
            try:
                with Image.open(fp) as im:
                    im = ImageOps.exif_transpose(im)
                    w, h = im.size
                return w >= h
            except:
                return False
        grouped = []
        i = 0
        n = len(image_paths)
        while i < n:
            if not is_horizontal(image_paths[i]):
                grouped.append([image_paths[i]])
                i += 1
            else:
                if i + 1 < n and is_horizontal(image_paths[i + 1]):
                    grouped.append([image_paths[i], image_paths[i + 1]])
                    i += 2
                else:
                    grouped.append([image_paths[i]])
                    i += 1
        total_images = sum(len(g) for g in grouped)
        self.pdf_progress_dialog = self.showProgress(total_images, "Creating PDF...")
        briefkopf_path = self.resource_path(os.path.join('resources', 'briefkopf.png'))
        self.pdf_worker = PDFCreationWorker(image_paths, aktennummer, dokumentenkürzel, dokumentenzahl, pdf_path, briefkopf_path, output_folder)
        self.pdf_worker.progressUpdate.connect(lambda val: self.pdf_progress_dialog.setValue(val))
        self.pdf_progress_dialog.canceled.connect(self.pdf_worker.cancel)
        self.pdf_worker.finished.connect(self.pdfFinished)
        self.pdf_worker.errorOccurred.connect(self.pdfError)
        self.pdf_worker.start()

    def pdfFinished(self, save_path):
        self.pdf_progress_dialog.close()
        QMessageBox.information(self, "PDF erstellt", f"PDF erfolgreich erstellt:\n{save_path}")
        if sys.platform == "win32":
            os.startfile(save_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", save_path])
        else:
            subprocess.run(["xdg-open", save_path])

    def pdfError(self, error_message):
        self.pdf_progress_dialog.close()
        QMessageBox.critical(self, "Fehler", f"Beim Erstellen der PDF ist ein Fehler aufgetreten:\n{error_message}")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("resources/icon.png"))
    translator = QTranslator()
    translations_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
    translator.load("qtbase_de", translations_path)
    app.installTranslator(translator)
    ex = ImageUploader()
    ex.show()
    sys.exit(app.exec())
