import sys
import logging
from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from modules.utils import setup_logging

def main():
    setup_logging()
    logger = logging.getLogger('Main')
    logger.info("Starting Nova Voice Assistant...")
    
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        
        sys.exit(app.exec())
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        print(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
