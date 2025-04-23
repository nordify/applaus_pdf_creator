import unittest
import os
import sys
import tempfile
import shutil
from PIL import Image
import PyPDF2

# Add the parent directory to the path so we can import the pdf_creator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_creator import PDFCreationWorker, ImageImportWorker
from PyQt6.QtCore import QEventLoop

class TestIntegration(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp()
        self.test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        self.briefkopf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "resources", "briefkopf.png")
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_output_dir)
    
    def test_image_import_to_pdf_creation(self):
        """Test the full workflow from image import to PDF creation."""
        # Get test images
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG")
        ]
        
        # First, import the images
        image_worker = ImageImportWorker(test_images)
        
        # Create a loop to wait for signals
        loop = QEventLoop()
        imported_images = []
        
        def on_image_imported(file_path, qimage):
            imported_images.append((file_path, qimage))
        
        def on_finished():
            loop.quit()
        
        image_worker.imageImported.connect(on_image_imported)
        image_worker.finished.connect(on_finished)
        
        # Start the worker and wait for it to finish
        image_worker.start()
        loop.exec()
        
        # Verify all images were imported
        self.assertEqual(len(imported_images), len(test_images), 
                       "All images should be imported")
        
        # Now create a PDF with the imported images
        pdf_path = os.path.join(self.test_output_dir, "integration_test.pdf")
        
        # Extract just the file paths from the imported images
        image_paths = [path for path, _ in imported_images]
        
        # Create a worker instance
        pdf_worker = PDFCreationWorker(
            image_paths=image_paths,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        pdf_worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify the PDF has the correct content
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            # We should have at least one page
            self.assertGreater(len(pdf_reader.pages), 0, 
                             "PDF should have at least one page")