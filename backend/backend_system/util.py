from datetime import datetime

def get_current_time():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

from datetime import datetime

def get_late_minute():
    # Giờ làm bắt đầu (có thể chỉnh theo ý bạn)
    work_time_str = datetime.now().strftime("%Y-%m-%d") + " 08:00:00"
    work_time = datetime.strptime(work_time_str, "%Y-%m-%d %H:%M:%S")

    # Thời gian hiện tại
    now = datetime.now()

    # Tính số phút đi muộn
    late_minutes = max(0, int((now - work_time).total_seconds() // 60))
    return late_minutes

def get_bonus_time():
    checkout_time_str = datetime.now().strftime("%Y-%m-%d") + " 17:00:00"
    checkout_time = datetime.strptime(checkout_time_str, "%Y-%m-%d %H:%M:%S")

    # Thời gian hiện tại
    now = datetime.now()

    # Tính số phút đi muộn
    bonus_time = max(0, int((now - checkout_time).total_seconds() // 60))
    return bonus_time
