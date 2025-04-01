from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QHBoxLayout, QMessageBox, QDialog, QFormLayout, QDoubleSpinBox
)
import pymongo

# Kết nối MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
salary_collection = db["salary"]

class SalaryTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # Nút tải dữ liệu lương
        self.load_button = QPushButton("Load Salary Data")
        self.load_button.clicked.connect(self.load_salary_data)
        layout.addWidget(self.load_button)

        # Bảng hiển thị dữ liệu lương (Không cho chỉnh sửa)
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Hệ số lương", "Số giờ làm", 
            "Số giờ làm OT", "Số phút đi muộn", "Nghỉ KP", "Nghỉ CP", "Tổng lương"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Không cho chỉnh sửa bảng
        layout.addWidget(self.table)

        # Khu vực tìm nhân viên để tăng lương
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter Employee ID")
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Tăng Lương")
        self.search_button.clicked.connect(self.show_raise_salary_dialog)
        search_layout.addWidget(self.search_button)

        layout.addLayout(search_layout)

        self.setLayout(layout)

    def load_salary_data(self):
        """Load danh sách lương từ MongoDB"""
        salary_data = salary_collection.find({})
        self.table.setRowCount(0)  # Xóa dữ liệu cũ trước khi tải mới

        for row_idx, salary in enumerate(salary_data):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(salary.get("employee_id", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(salary.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(salary.get("salary_factor", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(salary.get("work_hours", ""))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(str(salary.get("overtime_hours", ""))))
            self.table.setItem(row_idx, 5, QTableWidgetItem(str(salary.get("late_minutes", ""))))
            self.table.setItem(row_idx, 6, QTableWidgetItem(str(salary.get("absent_without_permission", ""))))
            self.table.setItem(row_idx, 7, QTableWidgetItem(str(salary.get("absent_with_permission", ""))))

            # Tính tổng lương
            total_salary = self.calculate_salary(salary)
            self.table.setItem(row_idx, 8, QTableWidgetItem(f"{total_salary:,.0f} VND"))

    def calculate_salary(self, salary):
        """Tính toán tổng lương"""
        base_salary = float(salary.get("base_salary", 50000))  # Lương cơ bản mỗi giờ
        overtime_rate = 1.5  # Hệ số OT
        late_penalty = 5000  # Phạt mỗi phút đi muộn
        absent_penalty = 100000  # Phạt mỗi ngày nghỉ không phép

        salary_factor = float(salary.get("salary_factor", 1))
        work_hours = float(salary.get("work_hours", 0))
        overtime_hours = float(salary.get("overtime_hours", 0))
        late_minutes = int(salary.get("late_minutes", 0))
        absent_without_permission = int(salary.get("absent_without_permission", 0))

        # Công thức tính lương
        total_salary = (
            salary_factor * (work_hours * base_salary) +
            (overtime_hours * base_salary * overtime_rate) -
            (late_minutes * late_penalty) -
            (absent_without_permission * absent_penalty)
        )

        return max(total_salary, 0)  # Đảm bảo không âm

    def show_raise_salary_dialog(self):
        """Hiển thị hộp thoại cập nhật lương cơ bản"""
        emp_id = self.search_input.text().strip()

        if not emp_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Employee ID!")
            return

        # Tìm nhân viên
        salary_data = salary_collection.find_one({"employee_id": emp_id})

        if not salary_data:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy nhân viên này!")
            return

        # Hiển thị dialog để cập nhật lương cơ bản
        dialog = RaiseSalaryDialog(salary_data)
        if dialog.exec():
            new_salary = dialog.new_salary_value
            salary_collection.update_one(
                {"employee_id": emp_id},
                {"$set": {"base_salary": new_salary}}
            )
            QMessageBox.information(self, "Thành công", "Lương cơ bản đã được cập nhật!")
            self.load_salary_data()  # Refresh bảng


class RaiseSalaryDialog(QDialog):
    """Hộp thoại cập nhật lương cơ bản"""
    def __init__(self, salary_data):
        super().__init__()
        self.setWindowTitle("Cập nhật lương cơ bản")

        layout = QFormLayout()

        self.emp_id = salary_data.get("employee_id", "")
        self.name = salary_data.get("name", "")
        self.old_salary = float(salary_data.get("base_salary", 50000))

        layout.addRow("Employee ID:", QLabel(self.emp_id))
        layout.addRow("Name:", QLabel(self.name))

        self.salary_input = QDoubleSpinBox()
        self.salary_input.setMinimum(1000)
        self.salary_input.setMaximum(1000000)
        self.salary_input.setValue(self.old_salary)
        layout.addRow("Lương cơ bản mới:", self.salary_input)

        self.update_button = QPushButton("Cập nhật")
        self.update_button.clicked.connect(self.accept)
        layout.addRow(self.update_button)

        self.setLayout(layout)

    @property
    def new_salary_value(self):
        return self.salary_input.value()
