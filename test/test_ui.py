import unittest
import os
import sys
import tempfile
import shutil
from PyQt6.QtWidgets import QApplication
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

# Add the parent directory to the path so we can import the pdf_creator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_creator import ImageUploader

class TestUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a QApplication instance
        cls.app = QApplication(sys.argv)
        
    @classmethod
    def tearDownClass(cls):
        # Clean up the QApplication instance
        cls.app.quit()
        # Process any remaining events
        cls.app.processEvents()
        
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp()
        self.test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        
        # Create the UI
        self.ui = ImageUploader()
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_output_dir)
        
    def test_initial_state(self):
        """Test the initial state of the UI."""
        # Verify the initial state of the UI
        self.assertEqual(self.ui.images, [], "Images list should be empty initially")
        self.assertFalse(self.ui.pdf_button.isEnabled(), "PDF button should be disabled initially")
        
    def test_input_validation(self):
        """Test input validation for required fields."""
        # Set valid inputs
        self.ui.aktennummer_input.setText("12345")
        self.ui.dokumentenzahl_input.setText("01")
        
        # Verify PDF button is still disabled without images
        self.assertFalse(self.ui.pdf_button.isEnabled(), "PDF button should be disabled without images")
        
        # Since we can't directly add images, we'll simulate it by directly modifying the images list
        # This is a test-only approach that doesn't require changing the application code
        test_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        
        # Create a mock frame and add it to the images list
        from PyQt6.QtWidgets import QFrame
        from PyQt6.QtGui import QPixmap
        mock_frame = QFrame()
        mock_pixmap = QPixmap()
        self.ui.images.append((mock_frame, test_image_path, mock_pixmap))
        
        # Call the method that updates the UI based on the images list
        self.ui.updateImageCounter()
        self.ui.updatePdfButtonState()
        
        # Verify PDF button is now enabled
        self.assertTrue(self.ui.pdf_button.isEnabled(), "PDF button should be enabled with valid inputs")
        
        # Clear aktennummer and verify button is disabled
        self.ui.aktennummer_input.setText("")
        self.ui.updatePdfButtonState()
        self.assertFalse(self.ui.pdf_button.isEnabled(), "PDF button should be disabled without aktennummer")
        
        # Restore aktennummer and clear dokumentenzahl
        self.ui.aktennummer_input.setText("12345")
        self.ui.dokumentenzahl_input.setText("")
        self.ui.updatePdfButtonState()
        self.assertFalse(self.ui.pdf_button.isEnabled(), "PDF button should be disabled without dokumentenzahl")
    
    def test_dokumentenkürzel_selection(self):
        """Test that the dokumentenkürzel dropdown works correctly."""
        # Verify initial selection is the placeholder
        self.assertEqual(self.ui.dokumentenkürzel_input.currentIndex(), 0, 
                        "Initial selection should be the placeholder")
        
        # Test selecting different values
        test_indices = [1, 2, 3]  # GA, ST, PR
        for idx in test_indices:
            self.ui.dokumentenkürzel_input.setCurrentIndex(idx)
            self.assertEqual(self.ui.dokumentenkürzel_input.currentIndex(), idx,
                           f"Selection should be set to index {idx}")
    
    def test_start_photo_number(self):
        """Test the start photo number input."""
        # Verify default value is "1"
        self.assertEqual(self.ui.start_photo_number.text(), "1", 
                        "Default start photo number should be 1")
        
        # Test setting valid values
        valid_values = ["2", "10", "999"]
        for val in valid_values:
            self.ui.start_photo_number.setText(val)
            self.assertEqual(self.ui.start_photo_number.text(), val,
                           f"Start photo number should be set to {val}")
    
    def test_reset_functionality(self):
        """Test that the reset button clears all inputs and images."""
        # Set some values
        self.ui.aktennummer_input.setText("12345")
        self.ui.dokumentenzahl_input.setText("01")
        self.ui.dokumentenkürzel_input.setCurrentIndex(2)  # Select "ST"
        
        # Add a mock image
        from PyQt6.QtWidgets import QFrame, QMessageBox
        from PyQt6.QtCore import QTimer
        mock_frame = QFrame()
        test_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        self.ui.images.append((mock_frame, test_image_path, "unique_id"))
        self.ui.updateImageCounter()
        
        # Set up a timer to automatically click "Yes" on the confirmation dialog
        def handle_dialog():
            # Find the message box and click "Yes"
            for widget in QApplication.topLevelWidgets():
                if isinstance(widget, QMessageBox) and widget.isVisible():
                    # Find the "Yes" button (usually button 0 in a Yes/No dialog)
                    yes_button = widget.buttons()[0]
                    QTest.mouseClick(yes_button, Qt.MouseButton.LeftButton)
                    break
        
        # Schedule the dialog handler to run shortly after we call resetApp
        QTimer.singleShot(100, handle_dialog)
        
        # Call reset (this will trigger the confirmation dialog)
        self.ui.resetApp()
        
        # Process events to make sure the dialog is handled
        QApplication.processEvents()
        
        # Verify everything is reset
        self.assertEqual(self.ui.aktennummer_input.text(), "", "Aktennummer should be cleared")
        self.assertEqual(self.ui.dokumentenzahl_input.text(), "", "Dokumentenzahl should be cleared")
        self.assertEqual(self.ui.images, [], "Images list should be empty")
        self.assertEqual(self.ui.image_counter_label.text(), "0 Bilder", "Image counter should be reset")

if __name__ == "__main__":
    unittest.main()