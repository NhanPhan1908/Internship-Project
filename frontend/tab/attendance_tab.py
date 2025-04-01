from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem
)
import pymongo

#connect DB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["Intern"]
attendance_collection = db["attendance"]

class AttendanceTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        # button load data
        self.load_button = QPushButton("Load Attendance")
        self.load_button.clicked.connect(self.load_attendance)
        layout.addWidget(self.load_button)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(5)  # 5 cột
        self.table.setHorizontalHeaderLabels([
            "Employee ID", "Name", "Confidence", "Embedding", "Thời gian"
        ])
        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_attendance(self):
        """Load dữ liệu điểm danh từ MongoDB"""
        records = attendance_collection.find({})
        self.table.setRowCount(0)  # clear odd data before loading new

        for row_idx, record in enumerate(records):
            self.table.insertRow(row_idx)
            self.table.setItem(row_idx, 0, QTableWidgetItem(record.get("employee_id", "")))
            self.table.setItem(row_idx, 1, QTableWidgetItem(record.get("name", "")))
            self.table.setItem(row_idx, 2, QTableWidgetItem(str(record.get("confidence", ""))))
            self.table.setItem(row_idx, 3, QTableWidgetItem(str(record.get("embedding", ""))))
            self.table.setItem(row_idx, 4, QTableWidgetItem(record.get("time", "")))

        #  no edit triggers
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
