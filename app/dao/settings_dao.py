from app.models import SystemSetting
from app import db


def get_setting(key):
    """Get a setting value by key"""
    setting = SystemSetting.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else None


def get_setting_int(key, default=0):
    """Get setting as integer"""
    value = get_setting(key)
    return int(value) if value else default


def get_setting_float(key, default=0.0):
    """Get setting as float"""
    value = get_setting(key)
    return float(value) if value else default


def set_setting(key, value):
    """Set a setting value (insert or update)"""
    setting = SystemSetting.query.filter_by(setting_key=key).first()
    if setting:
        setting.setting_value = str(value)
    else:
        setting = SystemSetting(setting_key=key, setting_value=str(value))
        db.session.add(setting)
    db.session.commit()
    return setting


def get_all_settings():
    """Get all settings as dict"""
    settings = SystemSetting.query.all()
    return {s.setting_key: s.setting_value for s in settings}
