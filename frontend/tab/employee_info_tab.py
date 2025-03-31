from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["attendance_system"]
employees_collection = db["employees"]

class EmployeeInfoTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Employee ID")
        layout.addWidget(self.id_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_employee)
        layout.addWidget(self.search_button)

        self.info_label = QLabel("")
        layout.addWidget(self.info_label)

        self.setLayout(layout)

    def search_employee(self):
        emp_id = self.id_input.text()
        emp = employees_collection.find_one({"employee_id": emp_id})
        if emp:
            self.info_label.setText(f"Name: {emp['name']}\nDepartment: {emp['department']}")
        else:
            self.info_label.setText("🚫 Employee not found!")
