from PyQt6.QtWidgets import QMainWindow, QTabWidget
from .face_recognition_tab import FaceRecognitionTab
from .employee_list_tab import EmployeeListTab
from .employee_info_tab import EmployeeInfoTab
from .salary_tab import SalaryTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Employee Management System")
        self.setGeometry(100, 100, 800, 600)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(FaceRecognitionTab(), "Face Recognition")
        self.tabs.addTab(EmployeeListTab(), "All Employees")
        self.tabs.addTab(EmployeeInfoTab(), "Employee Info")
        self.tabs.addTab(SalaryTab(), "Salary")
