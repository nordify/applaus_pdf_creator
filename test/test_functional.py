import unittest
import os
import sys
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication, QFileDialog
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_creator import ImageUploader

class TestFunctional(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
        
    def setUp(self):
        self.test_output_dir = tempfile.mkdtemp()
        self.test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        
        self.ui = ImageUploader()
        
    def tearDown(self):
        shutil.rmtree(self.test_output_dir)
    
    def test_end_to_end_workflow(self):
        """Test the complete workflow from UI input to PDF creation."""
        self.ui.aktennummer_input.setText("12345")
        self.ui.dokumentenzahl_input.setText("01")
        self.ui.dokumentenkürzel_input.setCurrentIndex(1)
        
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG")
        ]
        
        for img_path in test_images:
            from PyQt6.QtWidgets import QFrame
            mock_frame = QFrame()
            mock_pixmap = QPixmap(img_path)
            self.ui.images.append((mock_frame, img_path, mock_pixmap))
        
        self.ui.updateImageCounter()
        self.ui.updatePdfButtonState()
        
        self.assertEqual(len(self.ui.images), len(test_images), 
                       f"Expected {len(test_images)} images to be added")
        
        self.assertTrue(self.ui.pdf_button.isEnabled(), 
                      "PDF button should be enabled after adding images and setting required fields")
        
        original_getSaveFileName = QFileDialog.getSaveFileName
        pdf_output_path = os.path.join(self.test_output_dir, "12345-GA-01")
        QFileDialog.getSaveFileName = lambda *args, **kwargs: (pdf_output_path, "")
        
        def close_message_boxes():
            for widget in QApplication.topLevelWidgets():
                if widget.isVisible() and widget.metaObject().className() == "QMessageBox":
                    QTest.keyClick(widget, Qt.Key.Key_Enter)
        
        QTimer.singleShot(1000, close_message_boxes)
        
        QTest.mouseClick(self.ui.pdf_button, Qt.MouseButton.LeftButton)
        
        QFileDialog.getSaveFileName = original_getSaveFileName
        
        QApplication.processEvents()