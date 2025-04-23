import unittest
import os
import sys
import gc

# Add the parent directory to the path so we can import the test modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import test modules directly, not as submodules of test
from test_image_processing import TestImageProcessing
from test_pdf_creation import TestPDFCreation
from test_ui import TestUI
from test_integration import TestIntegration
from test_functional import TestFunctional

def run_tests():
    # Create a test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_suite.addTest(unittest.makeSuite(TestImageProcessing))
    test_suite.addTest(unittest.makeSuite(TestPDFCreation))
    test_suite.addTest(unittest.makeSuite(TestUI))
    test_suite.addTest(unittest.makeSuite(TestIntegration))
    test_suite.addTest(unittest.makeSuite(TestFunctional))
    
    # Run the tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    
    # Force garbage collection to clean up Qt objects
    gc.collect()
    
    # Exit with a delay to allow Qt to clean up properly
    from PyQt6.QtCore import QTimer, QCoreApplication
    import time
    
    # Give Qt time to process any pending events
    QCoreApplication.processEvents()
    
    # Sleep briefly to allow cleanup
    time.sleep(0.1)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)