from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QDateEdit, QSpinBox, QMessageBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate
import pymongo
import csv
from datetime import datetime

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
attendance_collection = db["attendance"]

class AttendanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_attendance()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Layout ---
        left_layout = QVBoxLayout()

        # Filter + Search layout
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Tìm theo tên hoặc ID...")
        self.search_input.textChanged.connect(self.load_attendance)
        filter_layout.addWidget(QLabel("🔍"))
        filter_layout.addWidget(self.search_input)

        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addDays(-7))
        self.date_from.dateChanged.connect(self.load_attendance)

        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        self.date_to.dateChanged.connect(self.load_attendance)

        self.confidence_filter = QSpinBox()
        self.confidence_filter.setRange(0, 100)
        self.confidence_filter.setValue(0)
        self.confidence_filter.valueChanged.connect(self.load_attendance)

        filter_layout.addWidget(QLabel("Từ:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("Đến:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QLabel("Conf ≥"))
        filter_layout.addWidget(self.confidence_filter)

        left_layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Employee ID", "Name", "Confidence", "Embedding", "Thời gian"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_layout.addWidget(self.table)

        # --- Right Layout ---
        right_layout = QVBoxLayout()

        self.export_button = QPushButton("📤 Xuất CSV")
        self.export_button.clicked.connect(self.export_csv)

        self.add_button = QPushButton("➕ Thêm bản ghi")
        self.add_button.clicked.connect(self.add_record)

        self.delete_button = QPushButton("🗑 Xoá bản ghi")
        self.delete_button.clicked.connect(self.delete_selected)

        self.refresh_button = QPushButton("🔄 Làm mới")
        self.refresh_button.clicked.connect(self.load_attendance)

        right_layout.addWidget(self.export_button)
        right_layout.addWidget(self.add_button)
        right_layout.addWidget(self.delete_button)
        right_layout.addWidget(self.refresh_button)

        right_layout.addSpacing(20)

        # Log layout
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Log thao tác sẽ hiển thị tại đây...")
        right_layout.addWidget(QLabel("📜 Log"))
        right_layout.addWidget(self.log_output)

        # Gắn layout trái và phải vào bố cục chính
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

    def log(self, text):
        """Ghi log vào log_output"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{timestamp} {text}")

    def load_attendance(self):
        self.table.setRowCount(0)
        query = {}

        text = self.search_input.text().strip().lower()
        if text:
            query["$or"] = [
                {"employee_id": {"$regex": text, "$options": "i"}},
                {"name": {"$regex": text, "$options": "i"}}
            ]

        from_date = self.date_from.date().toPyDate()
        to_date = self.date_to.date().toPyDate()
        to_date = datetime(to_date.year, to_date.month, to_date.day, 23, 59, 59)

        query["time"] = {
            "$gte": datetime(from_date.year, from_date.month, from_date.day),
            "$lte": to_date
        }

        confidence_min = self.confidence_filter.value()
        if confidence_min > 0:
            query["confidence"] = {"$gte": confidence_min}

        records = attendance_collection.find(query).sort("time", -1)

        for row_idx, record in enumerate(records):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(record.get("employee_id", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(record.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(record.get("confidence", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("embedding", ""))[:30] + "..."))
            self.table.setItem(row_idx, 4, QTableWidgetItem(record.get("time", "").strftime("%Y-%m-%d %H:%M:%S")))

        self.log("Đã load dữ liệu điểm danh.")

    def export_csv(self):
        path = "attendance_export.csv"
        with open(path, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            headers = ["Employee ID", "Name", "Confidence", "Embedding", "Time"]
            writer.writerow(headers)

            for row in range(self.table.rowCount()):
                data = [
                    self.table.item(row, col).text() for col in range(self.table.columnCount())
                ]
                writer.writerow(data)

        self.log(f"Xuất CSV thành công: {path}")
        QMessageBox.information(self, "Xuất CSV", f"Xuất dữ liệu thành công ra {path}")

    def add_record(self):
        now = datetime.now()
        new_record = {
            "employee_id": "EMP999",
            "name": "New Employee",
            "confidence": 95,
            "embedding": "[0.123, 0.456]",
            "time": now
        }
        attendance_collection.insert_one(new_record)
        self.log("Đã thêm bản ghi mới.")
        self.load_attendance()

    def delete_selected(self):
        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Xoá", "Vui lòng chọn một bản ghi để xoá.")
            return

        emp_id = self.table.item(selected, 0).text()
        time_str = self.table.item(selected, 4).text()
        time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

        result = attendance_collection.delete_one({
            "employee_id": emp_id,
            "time": time_obj
        })

        if result.deleted_count:
            self.log(f"Đã xoá bản ghi: {emp_id}")
            QMessageBox.information(self, "Xoá", "Đã xoá bản ghi.")
        else:
            self.log("Không tìm thấy bản ghi để xoá.")
            QMessageBox.warning(self, "Xoá", "Không tìm thấy bản ghi để xoá.")

        self.load_attendance()
