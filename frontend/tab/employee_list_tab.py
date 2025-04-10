from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QDialog, QFormLayout, QLineEdit, QMessageBox, QLabel, QTextEdit
)
from PyQt6.QtCore import Qt
import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
employees_collection = db["employees"]
salary_collection = db["salary"]

class EmployeeListTab(QWidget):
    def __init__(self):
        super().__init__()

        # === MAIN LAYOUT (Horizontal) ===
        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(10)

        # === LEFT LAYOUT ===
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(5, 5, 5, 5)
        left_layout.setSpacing(5)

        # --- Search Layout ---
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("  🔍 Tìm kiếm tên hoặc ID...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px 6px 24px;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #fff;
                font-size: 14px;
            }
        """)
        self.search_input.textChanged.connect(self.search_employees)
        search_layout.addWidget(self.search_input)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Department", "Position", "Phone", "Salary", "Address"
        ])
        self.table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                background-color: #fefefe;
            }
        """)
        self.table.setAlternatingRowColors(True)
        self.table.itemChanged.connect(self.update_employee)

        # Set column widths
        self.table.setColumnWidth(1, 200)  # Name
        self.table.setColumnWidth(6, 250)  # Address

        left_layout.addLayout(search_layout)
        left_layout.addWidget(self.table)

        # === RIGHT LAYOUT ===
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(5, 5, 5, 5)
        right_layout.setSpacing(10)

        # --- Buttons ---
        self.load_button = QPushButton("🔄 Load Employees")
        self.load_button.clicked.connect(self.load_employees)
        self.load_button.setStyleSheet("padding: 8px;")

        self.add_button = QPushButton("➕ Add Employee")
        self.add_button.clicked.connect(self.add_employee)
        self.add_button.setStyleSheet("padding: 8px;")

        right_layout.addWidget(self.load_button)
        right_layout.addWidget(self.add_button)

        # --- Log Area ---
        log_title = QLabel("📄 Log thao tác:")
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setStyleSheet("""
            QTextEdit {
                background-color: #fff;
                border: 1px solid #ccc;
                padding: 6px;
            }
        """)
        self.log_box.setFixedHeight(200)

        right_layout.addWidget(log_title)
        right_layout.addWidget(self.log_box)
        right_layout.addStretch()

        # Add both to main layout
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

        self.setLayout(main_layout)

    def load_employees(self):
        self.table.setRowCount(0)
        employees = employees_collection.find({})
        for row_idx, emp in enumerate(employees):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(emp.get("employee_id", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(emp.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(emp.get("department", "")))
            self.table.setItem(row_idx, 3, QTableWidgetItem(emp.get("position", "")))
            self.table.setItem(row_idx, 4, QTableWidgetItem(emp.get("phone", "")))

            salary = salary_collection.find_one({"employee_id": emp["employee_id"]})
            salary_amount = str(salary["base_salary"]) if salary else "0"
            self.table.setItem(row_idx, 5, QTableWidgetItem(salary_amount))
            self.table.setItem(row_idx, 6, QTableWidgetItem(emp.get("address", "")))

        self.log_box.append("✅ Danh sách nhân viên đã được tải.")

    def search_employees(self, text):
        text = text.lower()
        for row in range(self.table.rowCount()):
            match = False
            for col in [0, 1]:  # Search theo ID và Name
                item = self.table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            self.table.setRowHidden(row, not match)

    def add_employee(self):
        dialog = EmployeeFormDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if employees_collection.find_one({"employee_id": data["employee_id"]}):
                QMessageBox.warning(self, "Lỗi", "Employee ID đã tồn tại!")
                return

            employees_collection.insert_one(data)
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

            QMessageBox.information(self, "Thành công", "Đã thêm nhân viên!")
            self.log_box.append(f"➕ Đã thêm: {data['name']}")
            self.load_employees()

    def update_employee(self, item):
        row = item.row()
        col = item.column()
        emp_id = self.table.item(row, 0).text()

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
                self.log_box.append(f"💲 Lương của {emp_id} được cập nhật: {new_value}")
            except ValueError:
                QMessageBox.warning(self, "Lỗi", "Lương phải là số!")
                return
        else:
            employees_collection.update_one(
                {"employee_id": emp_id},
                {"$set": {field_name: new_value}}
            )
            self.log_box.append(f"✏️ {field_name} của {emp_id} được cập nhật: {new_value}")

# === Form Add Employee ===
class EmployeeFormDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thêm Nhân Viên")
        layout = QFormLayout()

        self.fields = {
            "employee_id": QLineEdit(),
            "name": QLineEdit(),
            "department": QLineEdit(),
            "position": QLineEdit(),
            "phone": QLineEdit(),
            "address": QLineEdit(),
            "salary": QLineEdit()
        }

        for label, widget in self.fields.items():
            layout.addRow(label.capitalize(), widget)

        self.submit_button = QPushButton("Thêm")
        self.submit_button.clicked.connect(self.accept)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def get_data(self):
        return {key: field.text().strip() for key, field in self.fields.items()}
