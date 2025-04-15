from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QLabel, QDateEdit, QSpinBox, QMessageBox, QTextEdit, QComboBox
)
from PyQt6.QtCore import Qt, QDate
import pymongo
import csv
from datetime import datetime
from collections import Counter

# --- Kết nối MongoDB với try-except ---
try:
    client = pymongo.MongoClient("mongodb://localhost:27017/", serverSelectionTimeoutMS=3000)
    client.server_info()  # Gọi để kiểm tra kết nối
    db = client["Intern"]
    attendance_collection = db["attendance"]
except Exception as e:
    attendance_collection = None
    print(f"❌ Không thể kết nối MongoDB: {e}")

class AttendanceTab(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_attendance()

    def init_ui(self):
        main_layout = QHBoxLayout(self)

        # --- Left Layout ---
        left_layout = QVBoxLayout()

        # Filter layout
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

        self.status_filter = QComboBox()
        self.status_filter.addItems(["Tất cả", "Có mặt", "Vắng"])
        self.status_filter.currentIndexChanged.connect(self.load_attendance)

        filter_layout.addWidget(QLabel("Từ:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("Đến:"))
        filter_layout.addWidget(self.date_to)
        filter_layout.addWidget(QLabel("Conf ≥"))
        filter_layout.addWidget(self.confidence_filter)
        filter_layout.addWidget(QLabel("Trạng thái:"))
        filter_layout.addWidget(self.status_filter)

        left_layout.addLayout(filter_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Employee ID", "Name", "Confidence", "Embedding", "Thời gian", "Trạng thái"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.cellClicked.connect(self.show_detail)
        left_layout.addWidget(self.table)

        # Stats
        self.stats_label = QLabel()
        left_layout.addWidget(self.stats_label)

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

        # Log
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setPlaceholderText("Log thao tác sẽ hiển thị tại đây...")
        right_layout.addWidget(QLabel("📜 Log"))
        right_layout.addWidget(self.log_output)

        # Combine layouts
        main_layout.addLayout(left_layout, 3)
        main_layout.addLayout(right_layout, 1)

    def log(self, text):
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        self.log_output.append(f"{timestamp} {text}")

    def load_attendance(self):
        self.table.setRowCount(0)

        if attendance_collection is None:
            self.log("❌ Không thể kết nối tới MongoDB.")
            QMessageBox.critical(self, "Lỗi kết nối", "Không thể kết nối tới MongoDB.")
            return

        try:
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

            if self.confidence_filter.value() > 0:
                query["confidence"] = {"$gte": self.confidence_filter.value()}

            status_val = self.status_filter.currentText()
            if status_val != "Tất cả":
                query["status"] = status_val

            records = list(attendance_collection.find(query).sort("time", -1))

            unique_names = set()
            counter_by_person = Counter()

            for row_idx, record in enumerate(records):
                self.table.insertRow(row_idx)

                emp_id = record.get("employee_id", "")
                name = record.get("name", "")
                confidence = record.get("confidence", "")
                embedding = str(record.get("embedding", ""))[:30] + "..."
                time_val = record.get("time", "")
                status = record.get("status", "")

                time_str = time_val.strftime("%Y-%m-%d %H:%M:%S") if isinstance(time_val, datetime) else str(time_val)

                for col, val in enumerate([emp_id, name, confidence, embedding, time_str, status]):
                    item = QTableWidgetItem(str(val))
                    item.setToolTip(str(val))
                    self.table.setItem(row_idx, col, item)

                unique_names.add(emp_id)
                counter_by_person[emp_id] += 1

            self.stats_label.setText(f"🔢 Tổng bản ghi: {len(records)} | 👤 Người duy nhất: {len(unique_names)}")
            self.log("✅ Đã load dữ liệu điểm danh.")
        except Exception as e:
            self.log(f"❌ Lỗi khi load dữ liệu: {e}")
            QMessageBox.critical(self, "Lỗi tải dữ liệu", f"Lỗi khi tải dữ liệu từ MongoDB:\n{e}")

    def export_csv(self):
        try:
            path = "attendance_export.csv"
            with open(path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                headers = ["Employee ID", "Name", "Confidence", "Embedding", "Time", "Status"]
                writer.writerow(headers)

                for row in range(self.table.rowCount()):
                    data = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
                    writer.writerow(data)

            self.log(f"✅ Xuất CSV thành công: {path}")
            QMessageBox.information(self, "Xuất CSV", f"Xuất dữ liệu thành công ra {path}")
        except Exception as e:
            self.log(f"❌ Xuất CSV thất bại: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể xuất CSV:\n{e}")

    def add_record(self):
        if attendance_collection is None:
            QMessageBox.critical(self, "Lỗi", "Không thể kết nối MongoDB.")
            return
        try:
            now = datetime.now()
            new_record = {
                "employee_id": "EMP999",
                "name": "New Employee",
                "confidence": 95,
                "embedding": "[0.123, 0.456]",
                "time": now,
                "status": "Có mặt"
            }
            attendance_collection.insert_one(new_record)
            self.log("✅ Đã thêm bản ghi mới.")
            self.load_attendance()
        except Exception as e:
            self.log(f"❌ Lỗi thêm bản ghi: {e}")
            QMessageBox.critical(self, "Lỗi", f"Không thể thêm bản ghi:\n{e}")

    def delete_selected(self):
        if attendance_collection is None:
            QMessageBox.critical(self, "Lỗi", "Không thể kết nối MongoDB.")
            return

        selected = self.table.currentRow()
        if selected == -1:
            QMessageBox.warning(self, "Xoá", "Vui lòng chọn một bản ghi để xoá.")
            return

        try:
            emp_id = self.table.item(selected, 0).text()
            time_str = self.table.item(selected, 4).text()
            time_obj = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")

            result = attendance_collection.delete_one({
                "employee_id": emp_id,
                "time": time_obj
            })

            if result.deleted_count:
                self.log(f"🗑 Đã xoá bản ghi: {emp_id}")
                QMessageBox.information(self, "Xoá", "Đã xoá bản ghi.")
            else:
                self.log("⚠️ Không tìm thấy bản ghi để xoá.")
                QMessageBox.warning(self, "Xoá", "Không tìm thấy bản ghi để xoá.")

            self.load_attendance()
        except Exception as e:
            self.log(f"❌ Lỗi khi xoá: {e}")
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi xoá bản ghi:\n{e}")

    def show_detail(self, row, col):
        detail = ""
        for i in range(self.table.columnCount()):
            col_name = self.table.horizontalHeaderItem(i).text()
            val = self.table.item(row, i).text()
            detail += f"{col_name}: {val}\n"
        QMessageBox.information(self, "Chi tiết bản ghi", detail)
