from PyQt6.QtWidgets import QMainWindow, QTabWidget
from .face_recognition_tab import FaceRecognitionTab
from .employee_list_tab import EmployeeListTab
from .attendance_tab import AttendanceTab
from .salary_tab import SalaryTab
from .employee_register import EmployeeRegisterTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance checking System by Recognition Face")
        self.setGeometry(100, 100, 2500, 2600)

        self.tabs = QTabWidget(self)
        self.setCentralWidget(self.tabs)

        self.tabs.addTab(FaceRecognitionTab(), "Face Recognition")
        self.tabs.addTab(EmployeeRegisterTab(), "Employee Register")
        self.tabs.addTab(EmployeeListTab(), "All Employees")
        self.tabs.addTab(AttendanceTab(), "Attendance")
        self.tabs.addTab(SalaryTab(), "Salary")
