from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox
)
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
employees_collection = db["employees"]
salary_collection = db["salary"]  

class EmployeeListTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # button load dât
        self.load_button = QPushButton("Load Employees")
        self.load_button.clicked.connect(self.load_employees)
        layout.addWidget(self.load_button)

        # button add data
        self.add_button = QPushButton("Add Employee")
        self.add_button.clicked.connect(self.add_employee)
        layout.addWidget(self.add_button)

        # table
        self.table = QTableWidget()
        self.table.setColumnCount(7)  # 7 cột
        self.table.setHorizontalHeaderLabels(
            ["Employee ID", "Name", "Department", "Position", "Phone", "Salary", "Address"]
        )
        layout.addWidget(self.table)

        # update data
        self.table.itemChanged.connect(self.update_employee)

        self.setLayout(layout)

    def load_employees(self):
        """Load danh sách nhân viên từ MongoDB"""
        employees = employees_collection.find({})
        self.table.setRowCount(0)  # delete old data before loading new

        for row_idx, emp in enumerate(employees):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(emp.get("employee_id", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(emp.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(emp.get("department", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(emp.get("position", "")))
            self.table.setItem(row_idx, 4, QTableWidgetItem(emp.get("phone", "")))

            # take datas from salary collection
            salary = salary_collection.find_one({"employee_id": emp["employee_id"]})
            salary_amount = str(salary["base_salary"]) if salary else "0"
            self.table.setItem(row_idx, 5, QTableWidgetItem(salary_amount))  

            self.table.setItem(row_idx, 6, QTableWidgetItem(emp.get("address", "")))

    def add_employee(self):
        """Hiển thị form nhập thông tin nhân viên mới"""
        dialog = EmployeeFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()

            if employees_collection.find_one({"employee_id": data["employee_id"]}):
                QMessageBox.warning(self, "Error", "Employee ID already exists!")
                return

            # add employee to collection `employees`
            employees_collection.insert_one(data)

            # when add a new employee, also add based-data to collection `salary`
            salary_collection.insert_one({
                "employee_id": data["employee_id"],
                "name": data["name"],
                "salary_factor": 1.0,
                "work_hours": 0,
                "overtime_hours": 0,
                "late_minutes": 0,
                "absent_without_permission": 0,
                "absent_with_permission": 0,
                "base_salary": float(data["salary"]) if data["salary"] else 5000000  
            })

            QMessageBox.information(self, "Success", "Employee added successfully!")
            self.load_employees()  # Update the table after adding a new employee

    def update_employee(self, item):
        """Cập nhật dữ liệu vào MongoDB khi chỉnh sửa trực tiếp trên bảng"""
        row = item.row()
        col = item.column()
        emp_id = self.table.item(row, 0).text()  # main key

        #define which column to update
        field_map = ["employee_id", "name", "department", "position", "phone", "salary", "address"]
        field_name = field_map[col]
        new_value = item.text()

    
        if field_name == "salary":
            try:
                new_value = float(new_value)
                salary_collection.update_one(
                    {"employee_id": emp_id},
                    {"$set": {"base_salary": new_value}}
                )
            except ValueError:
                QMessageBox.warning(self, "Error", "Salary must be a number!")
                return
        else:
            employees_collection.update_one(
                {"employee_id": emp_id},
                {"$set": {field_name: new_value}}
            )

# form add new employee
class EmployeeFormDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Add Employee")
        layout = QFormLayout()

        self.fields = {
            "employee_id": QLineEdit(),
            "name": QLineEdit(),
            "department": QLineEdit(),
            "position": QLineEdit(),
            "phone": QLineEdit(),
            "address": QLineEdit(),
            "salary": QLineEdit(),         
        }

        for label, widget in self.fields.items():
            layout.addRow(label.capitalize(), widget)

        self.submit_button = QPushButton("Add")
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def get_data(self):
        return {key: field.text().strip() for key, field in self.fields.items()}
