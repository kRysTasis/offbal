from datetime import (
    datetime,
    timezone,
    timedelta
)
from django.utils import timezone as tz


def utc_to_jst(timestamp_utc):
    """
    日時データのUTCをJSTに変換するメソッド
    """
    datetime_jst = timestamp_utc.astimezone(timezone(timedelta(hours=+9)))
    timestamp_jst = datetime.strftime(datetime_jst, '%Y-%m-%d %H:%M:%S')
    return timestamp_jst


class ReturnDateTime():
    '''
    日付等を返却するときに利用するクラス
    '''
    # 先週
    last_week = tz.now().date() - timedelta(days=7)
    # 先週の月曜
    monday_of_last_week = last_week - timedelta(days=(last_week.isocalendar()[2] -1))

    @classmethod
    def get_monday_of_this_week(cls):
        '''
        今週の月曜日を返却
        '''
        return cls.monday_of_last_week + timedelta(days=7)

    @classmethod
    def get_sunday_of_this_week(cls):
        '''
        今週の日曜日を返却
        '''
        return cls.get_monday_of_this_week() + timedelta(days=6)