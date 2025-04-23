import unittest
import os
import shutil
import sys
import tempfile
import PyPDF2
from PIL import Image

# Add the parent directory to the path so we can import the pdf_creator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_creator import PDFCreationWorker

class TestPDFCreation(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp()
        self.test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        self.briefkopf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "resources", "briefkopf.png")
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_output_dir)
    
    def test_pdf_creation_with_vertical_images(self):
        """Test PDF creation with vertical images."""
        # Get vertical test images
        vertical_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 04.JPG")
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "vertical_test.pdf")
        
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=vertical_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify the PDF has the correct number of pages
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            self.assertEqual(len(pdf_reader.pages), len(vertical_images), 
                           "PDF should have one page per vertical image")
    
    def test_pdf_creation_with_horizontal_images(self):
        """Test PDF creation with horizontal images."""
        # Get horizontal test images
        horizontal_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 02.JPG")
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "horizontal_test.pdf")
        
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=horizontal_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify the PDF has the correct number of pages (2 horizontal images can fit on 1 page)
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            # The number of pages should be ceil(len(horizontal_images) / 2)
            expected_pages = (len(horizontal_images) + 1) // 2
            self.assertEqual(len(pdf_reader.pages), expected_pages, 
                           "PDF should have the correct number of pages for horizontal images")
    
    def test_pdf_creation_with_mixed_images(self):
        """Test PDF creation with a mix of vertical and horizontal images."""
        # Get mixed test images
        mixed_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),  # Horizontal
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG"),  # Vertical
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 02.JPG"),  # Horizontal
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 04.JPG")   # Vertical
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "mixed_test.pdf")
        
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=mixed_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify all images were saved to the output folder
        for i in range(1, len(mixed_images) + 1):
            expected_output_path = os.path.join(self.test_output_dir, f"12345-UB-01 Foto Nr. {i}.JPG")
            self.assertTrue(os.path.exists(expected_output_path), 
                           f"Image should be saved at {expected_output_path}")
    
    def test_custom_start_photo_number(self):
        """Test PDF creation with a custom starting photo number."""
        # Get test images
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 02.JPG")
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "custom_start_test.pdf")
        
        # Create a worker instance with custom start number
        start_number = 5
        worker = PDFCreationWorker(
            image_paths=test_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir,
            start_photo_number=start_number
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify images were saved with the correct numbering
        for i in range(len(test_images)):
            expected_output_path = os.path.join(self.test_output_dir, 
                                              f"12345-UB-01 Foto Nr. {start_number + i}.JPG")
            self.assertTrue(os.path.exists(expected_output_path), 
                           f"Image should be saved with number {start_number + i}")
    
    def test_pdf_creation_without_dokumentenkürzel(self):
        """Test PDF creation without a dokumentenkürzel."""
        # Get test images
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "no_kürzel_test.pdf")
        
        # Create a worker instance with placeholder dokumentenkürzel
        worker = PDFCreationWorker(
            image_paths=test_images,
            aktennummer="12345",
            dokumentenkürzel="(Dokumentenkürzel auswählen oder leer lassen)",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was created
        self.assertTrue(os.path.exists(pdf_path), f"PDF should exist at {pdf_path}")
        
        # Verify images were saved with the correct naming format (without dokumentenkürzel)
        expected_output_path = os.path.join(self.test_output_dir, "12345-01 Foto Nr. 1.JPG")
        self.assertTrue(os.path.exists(expected_output_path), 
                       "Image should be saved without dokumentenkürzel in the filename")
    
    def test_worker_cancellation(self):
        """Test that the worker can be cancelled."""
        # Get a lot of test images to make the process take longer
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 02.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 04.JPG")
        ] * 3  # Repeat the images to make the process longer
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "cancel_test.pdf")
        
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=test_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Cancel the worker immediately
        worker.cancel()
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was not created (since we cancelled)
        self.assertFalse(os.path.exists(pdf_path), 
                        "PDF should not be created when worker is cancelled")

    def test_empty_image_list(self):
        """Test that the worker handles an empty image list gracefully."""
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "empty_test.pdf")
        
        # Create a worker instance with an empty image list
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Run the worker
        worker.run()
        
        # Verify the PDF was not created (since there are no images)
        self.assertFalse(os.path.exists(pdf_path), 
                        "PDF should not be created when there are no images")
    
    def test_missing_briefkopf(self):
        """Test that the worker handles a missing briefkopf file gracefully."""
        # Get test images
        test_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        ]
        
        # Create PDF path
        pdf_path = os.path.join(self.test_output_dir, "missing_briefkopf_test.pdf")
        
        # Create a worker instance with a non-existent briefkopf path
        worker = PDFCreationWorker(
            image_paths=test_images,
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path=pdf_path,
            briefkopf_path="non_existent_briefkopf.png",
            output_folder=self.test_output_dir
        )
        
        # Run the worker and check if it handles the error gracefully
        # This should not raise an exception, but the PDF should not be created
        worker.run()
        self.assertFalse(os.path.exists(pdf_path), 
                        "PDF should not be created when briefkopf is missing")

if __name__ == "__main__":
    unittest.main()