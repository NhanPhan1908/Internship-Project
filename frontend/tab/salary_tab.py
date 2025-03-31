from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QPushButton, QLabel
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["attendance_system"]
salary_collection = db["salary"]

class SalaryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter Employee ID")
        layout.addWidget(self.id_input)

        self.check_button = QPushButton("Check Salary")
        self.check_button.clicked.connect(self.check_salary)
        layout.addWidget(self.check_button)

        self.salary_label = QLabel("")
        layout.addWidget(self.salary_label)

        self.setLayout(layout)

    def check_salary(self):
        emp_id = self.id_input.text()
        salary = salary_collection.find_one({"employee_id": emp_id})
        if salary:
            self.salary_label.setText(f"💰 Salary: {salary['amount']} VND")
        else:
            self.salary_label.setText("🚫 No salary record found!")
