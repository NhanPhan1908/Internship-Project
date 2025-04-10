# salary_tab_extended.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QLabel, QComboBox, QSpinBox, QFileDialog, QMessageBox, QFormLayout, QDialog, QDoubleSpinBox
)
from PyQt6.QtCore import Qt
import pymongo
import csv
import pandas as pd
from fpdf import FPDF
import matplotlib.pyplot as plt
from io import BytesIO

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
salary_collection = db["salary"]

class SalaryTab(QWidget):
    def __init__(self):
        super().__init__()

        # Main Layout
        main_layout = QHBoxLayout()
        left_layout = QVBoxLayout()
        right_layout = QVBoxLayout()

        # === Search + Filter Layout ===
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Nhập tên hoặc ID")
        search_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tất cả", "Hệ số >=", "Tổng lương >=", "Giờ làm >="])
        search_layout.addWidget(self.filter_combo)

        self.filter_value = QSpinBox()
        self.filter_value.setMaximum(1000000)
        search_layout.addWidget(self.filter_value)

        self.search_button = QPushButton("Lọc")
        self.search_button.clicked.connect(self.apply_filter)
        search_layout.addWidget(self.search_button)

        left_layout.addLayout(search_layout)

        # === Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Hệ số lương", "Số giờ làm",
            "Số giờ làm OT", "Số phút đi muộn", "Nghỉ KP", "Nghỉ CP", "Tổng lương"
        ])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.table)

        # === Statistic Label ===
        self.stat_label = QLabel("Tổng nhân viên: 0 | Tổng lương: 0 | Lương TB: 0")
        left_layout.addWidget(self.stat_label)

        # === Button Layout ===
        self.load_button = QPushButton("Tải dữ liệu")
        self.load_button.clicked.connect(self.load_salary_data)

        self.export_button = QPushButton("Xuất CSV")
        self.export_button.clicked.connect(self.export_to_csv)

        self.chart_button = QPushButton("Biểu đồ lương")
        self.chart_button.clicked.connect(self.show_salary_chart)

        self.raise_button = QPushButton("Tăng lương")
        self.raise_button.clicked.connect(self.show_raise_salary_dialog)

        self.import_button = QPushButton("Nhập từ CSV")
        self.import_button.clicked.connect(self.import_csv)

        right_layout.addWidget(self.load_button)
        right_layout.addWidget(self.export_button)
        right_layout.addWidget(self.chart_button)
        right_layout.addWidget(self.raise_button)
        right_layout.addWidget(self.import_button)

        # === Logs ===
        self.log_label = QLabel("[Logs]")
        self.log_label.setWordWrap(True)
        right_layout.addWidget(self.log_label)

        # Combine layouts
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)
        self.setLayout(main_layout)

        # Auto load
        self.load_salary_data()

    def log(self, msg):
        self.log_label.setText(f"[Logs] {msg}")

    def load_salary_data(self):
        salary_data = salary_collection.find({})
        self.table.setRowCount(0)

        total = 0
        count = 0
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

            total_salary = self.calculate_salary(salary)
            self.table.setItem(row_idx, 8, QTableWidgetItem(f"{total_salary:,.0f}"))
            total += total_salary
            count += 1

        avg = total / count if count else 0
        self.stat_label.setText(f"Tổng nhân viên: {count} | Tổng lương: {total:,.0f} | Lương TB: {avg:,.0f}")
        self.log("Đã tải dữ liệu lương")

    def calculate_salary(self, salary):
        base_salary = float(salary.get("base_salary", 50000))
        overtime_rate = 1.5
        late_penalty = 5000
        absent_penalty = 100000

        factor = float(salary.get("salary_factor", 1))
        work_hours = float(salary.get("work_hours", 0))
        overtime_hours = float(salary.get("overtime_hours", 0))
        late_minutes = int(salary.get("late_minutes", 0))
        absent = int(salary.get("absent_without_permission", 0))

        total = (factor * work_hours * base_salary) + (overtime_hours * base_salary * overtime_rate) - (late_minutes * late_penalty) - (absent * absent_penalty)
        return max(total, 0)

    def apply_filter(self):
        keyword = self.search_input.text().lower()
        filter_type = self.filter_combo.currentText()
        value = self.filter_value.value()

        for row in range(self.table.rowCount()):
            match = True
            name = self.table.item(row, 1).text().lower()
            emp_id = self.table.item(row, 0).text().lower()
            factor = float(self.table.item(row, 2).text())
            hours = float(self.table.item(row, 3).text())
            total_salary = float(self.table.item(row, 8).text().replace(",", ""))

            if keyword not in name and keyword not in emp_id:
                match = False
            elif filter_type == "Hệ số >=" and factor < value:
                match = False
            elif filter_type == "Tổng lương >=" and total_salary < value:
                match = False
            elif filter_type == "Giờ làm >=" and hours < value:
                match = False

            self.table.setRowHidden(row, not match)

        self.log("Đã áp dụng bộ lọc")

    def export_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Lưu CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        with open(path, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            headers = [self.table.horizontalHeaderItem(i).text() for i in range(self.table.columnCount())]
            writer.writerow(headers)

            for row in range(self.table.rowCount()):
                if self.table.isRowHidden(row):
                    continue
                row_data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                writer.writerow(row_data)

        self.log(f"Đã xuất CSV: {path}")

    def show_salary_chart(self):
        names = []
        totals = []
        for row in range(self.table.rowCount()):
            if self.table.isRowHidden(row):
                continue
            name = self.table.item(row, 1).text()
            total = float(self.table.item(row, 8).text().replace(",", ""))
            names.append(name)
            totals.append(total)

        plt.barh(names, totals)
        plt.xlabel("Tổng lương")
        plt.ylabel("Tên")
        plt.title("Biểu đồ tổng lương")
        plt.tight_layout()
        plt.show()

    def show_raise_salary_dialog(self):
        emp_id = self.search_input.text().strip()
        if not emp_id:
            QMessageBox.warning(self, "Lỗi", "Vui lòng nhập Employee ID!")
            return

        salary_data = salary_collection.find_one({"employee_id": emp_id})
        if not salary_data:
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy nhân viên này!")
            return

        dialog = RaiseSalaryDialog(salary_data)
        if dialog.exec():
            new_salary = dialog.new_salary_value
            salary_collection.update_one({"employee_id": emp_id}, {"$set": {"base_salary": new_salary}})
            self.log("Đã cập nhật lương cơ bản")
            self.load_salary_data()

    def import_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn file CSV", "", "CSV Files (*.csv)")
        if not path:
            return

        df = pd.read_csv(path)
        records = df.to_dict(orient='records')
        for record in records:
            salary_collection.update_one({"employee_id": record.get("employee_id")}, {"$set": record}, upsert=True)

        self.log("Đã nhập dữ liệu từ CSV")
        self.load_salary_data()

class RaiseSalaryDialog(QDialog):
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
