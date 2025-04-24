import unittest
import os
import sys
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_image_processing import TestImageProcessing
from test_pdf_creation import TestPDFCreation
from test_ui import TestUI
from test_integration import TestIntegration
from test_functional import TestFunctional

def run_tests():
    test_suite = unittest.TestSuite()
    
    loader = unittest.TestLoader()
    test_suite.addTests(loader.loadTestsFromTestCase(TestImageProcessing))
    test_suite.addTests(loader.loadTestsFromTestCase(TestPDFCreation))
    test_suite.addTests(loader.loadTestsFromTestCase(TestUI))
    test_suite.addTests(loader.loadTestsFromTestCase(TestIntegration))
    test_suite.addTests(loader.loadTestsFromTestCase(TestFunctional))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    if sys.version_info.major != 3 or sys.version_info.minor != 13:
        print(f"Warning: Tests are designed for Python 3.13, but you're using Python {sys.version_info.major}.{sys.version_info.minor}")
    
    success = run_tests()
    
    gc.collect()
    
    from PyQt6.QtCore import QTimer, QCoreApplication
    import time
    
    QCoreApplication.processEvents()
    
    time.sleep(0.1)
    
    sys.exit(0 if success else 1)