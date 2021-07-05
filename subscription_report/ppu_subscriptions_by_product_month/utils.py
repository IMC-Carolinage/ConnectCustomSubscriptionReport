from datetime import datetime, timedelta


def now_str():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def get_first_day_last_month():
    if datetime.today().month == 1:
        datetime(datetime.today().year - 1, 12, 1, 8, 0, 0)
    else:
        return datetime(datetime.today().year, datetime.today().month - 1, 1, 8, 0, 0)


def get_last_day_last_month():
    return datetime(datetime.today().year, datetime.today().month, 1, 8, 0, 0) - timedelta(days=1)


def last_month_period_str():
    return get_first_day_last_month().strftime('%m/%d/%Y') + "-" + get_last_day_last_month().strftime('%m/%d/%Y')
