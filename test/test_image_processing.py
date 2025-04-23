import unittest
import os
import shutil
from PIL import Image, ImageOps
import sys
import tempfile

# Add the parent directory to the path so we can import the pdf_creator module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pdf_creator import PDFCreationWorker

class TestImageProcessing(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for test outputs
        self.test_output_dir = tempfile.mkdtemp()
        self.test_images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
        self.briefkopf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "resources", "briefkopf.png")
        
    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.test_output_dir)
        
    def test_is_horizontal(self):
        """Test the is_horizontal method for correctly identifying image orientation."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Test with horizontal image
        horizontal_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        self.assertTrue(worker.is_horizontal(horizontal_image_path), 
                       f"Image {horizontal_image_path} should be identified as horizontal")
        
        # Test with vertical image
        vertical_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 03.JPG")
        self.assertFalse(worker.is_horizontal(vertical_image_path), 
                        f"Image {vertical_image_path} should be identified as vertical")
    
    def test_process_image(self):
        """Test that processImage correctly processes and saves images."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Process a test image
        test_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 04.JPG")
        processed_path = worker.processImage(test_image_path, 1)
        
        # Verify the processed image exists
        self.assertTrue(os.path.exists(processed_path), 
                       f"Processed image should exist at {processed_path}")
        
        # Verify the original image was saved to the output folder
        expected_output_path = os.path.join(self.test_output_dir, "12345-UB-01 Foto Nr. 1.JPG")
        self.assertTrue(os.path.exists(expected_output_path), 
                       f"Original image should be saved at {expected_output_path}")
        
        # Verify the image orientation is correct
        with Image.open(processed_path) as img:
            width, height = img.size
            # The processed image should maintain proper orientation
            if not worker.is_horizontal(test_image_path):
                self.assertTrue(height > width, 
                              f"Vertical image should maintain vertical orientation")
            else:
                self.assertTrue(width >= height, 
                              f"Horizontal image should maintain horizontal orientation")
    
    def test_exif_orientation(self):
        """Test that EXIF orientation is correctly applied to saved images."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Process images with different EXIF orientations
        test_images = [
            "22498-UB-01 Foto Nr. 03.JPG",  # Vertical image
            "22498-UB-01 Foto Nr. 04.JPG"   # Another vertical image with different EXIF data
        ]
        
        for i, img_name in enumerate(test_images):
            test_image_path = os.path.join(self.test_images_dir, img_name)
            processed_path = worker.processImage(test_image_path, i+1)
            
            # Open the original image with EXIF orientation applied
            with Image.open(test_image_path) as original:
                original = ImageOps.exif_transpose(original)
                original_width, original_height = original.size
                original_orientation = "vertical" if original_height > original_width else "horizontal"
            
            # Open the processed image
            with Image.open(processed_path) as processed:
                processed_width, processed_height = processed.size
                processed_orientation = "vertical" if processed_height > processed_width else "horizontal"
            
            # The orientation should be preserved
            self.assertEqual(original_orientation, processed_orientation, 
                           f"Image {img_name} orientation should be preserved")
    
    def test_image_resizing(self):
        """Test that large images are properly resized."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Process a test image
        test_image_path = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        processed_path = worker.processImage(test_image_path, 1)
        
        # Check if the processed image is properly sized
        with Image.open(processed_path) as img:
            width, height = img.size
            max_side = max(width, height)
            self.assertLessEqual(max_side, 2000, 
                               "Large images should be resized to have max dimension of 2000px")
    
    def test_aspect_ratio_adjustment(self):
        """Test that aspect ratio adjustment works correctly for certain images."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Process horizontal images
        horizontal_images = [
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG"),
            os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 02.JPG")
        ]
        
        for i, img_path in enumerate(horizontal_images):
            processed_path = worker.processImage(img_path, i+1)
            
            # Check if the processed image has the correct aspect ratio
            with Image.open(processed_path) as img:
                width, height = img.size
                aspect_ratio = width / height
                
                # For horizontal images with aspect ratio between 1.0 and 1.33,
                # the code should adjust to 4:3 ratio
                if 1.0 <= aspect_ratio <= 1.33:
                    self.assertAlmostEqual(aspect_ratio, 4/3, delta=0.1, msg="Horizontal images should be adjusted to 4:3 aspect ratio")
    
    def test_different_dokumentenkürzel_formats(self):
        """Test that different dokumentenkürzel formats produce correct filenames."""
        # Test with normal dokumentenkürzel
        worker1 = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Test with placeholder dokumentenkürzel (starts with "(")
        worker2 = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="(Dokumentenkürzel auswählen oder leer lassen)",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        test_image = os.path.join(self.test_images_dir, "22498-UB-01 Foto Nr. 01.JPG")
        
        # Process with normal dokumentenkürzel
        processed_path1 = worker1.processImage(test_image, 1)
        expected_path1 = os.path.join(self.test_output_dir, "12345-UB-01 Foto Nr. 1.JPG")
        self.assertTrue(os.path.exists(expected_path1), 
                       "Image should be saved with dokumentenkürzel in the filename")
        
        # Process with placeholder dokumentenkürzel
        processed_path2 = worker2.processImage(test_image, 2)
        expected_path2 = os.path.join(self.test_output_dir, "12345-01 Foto Nr. 2.JPG")
        self.assertTrue(os.path.exists(expected_path2), 
                       "Image should be saved without dokumentenkürzel in the filename")

    def test_image_format_conversion(self):
        """Test that images with alpha channels (RGBA) are properly converted to RGB."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Create a test RGBA image
        test_image = Image.new('RGBA', (100, 100), (255, 0, 0, 128))
        test_image_path = os.path.join(self.test_output_dir, "test_rgba.png")
        test_image.save(test_image_path)
        
        # Process the RGBA image
        processed_path = worker.processImage(test_image_path, 1)
        
        # Verify the processed image exists and has been converted to RGB
        with Image.open(processed_path) as img:
            self.assertEqual(img.mode, "RGB", "RGBA image should be converted to RGB")
    
    def test_error_handling_invalid_image(self):
        """Test that the processImage method handles invalid image files gracefully."""
        # Create a worker instance
        worker = PDFCreationWorker(
            image_paths=[],
            aktennummer="12345",
            dokumentenkürzel="UB",
            dokumentenzahl="01",
            pdf_path="test.pdf",
            briefkopf_path=self.briefkopf_path,
            output_folder=self.test_output_dir
        )
        
        # Create an invalid "image" file
        invalid_image_path = os.path.join(self.test_output_dir, "invalid.jpg")
        with open(invalid_image_path, 'w') as f:
            f.write("This is not an image file")
        
        # Process should return the original path for invalid images
        result_path = worker.processImage(invalid_image_path, 1)
        self.assertEqual(result_path, invalid_image_path, 
                       "For invalid images, the original path should be returned")

if __name__ == "__main__":
    unittest.main()