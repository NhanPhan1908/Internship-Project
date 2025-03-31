from PyQt6.QtWidgets import QApplication
from tab.dashboard import MainWindow
import sys

app = QApplication(sys.argv)
window = MainWindow()
window.show()
sys.exit(app.exec())
