import json
from typing import TypedDict, Any
from sys import platform as PLATFORM
from framework.utils.helpers import AnyJson
from framework.core.base_settings import BaseSettings, runtime_imports, MissingKeyClass, _missing, SettingException, BaseSettingsDict

if PLATFORM == 'emscripten':
    from platform import window

class SettingsDict(BaseSettingsDict):
    Brightness : int

DEFAULT_SETTINGS : SettingsDict = {
    "Brightness" : 0
}

class Settings(BaseSettings):
    default : SettingsDict = DEFAULT_SETTINGS

    def __init__(self) -> None:
        self.brightness : int = self.default['Brightness']
    
    def reset(self):
        self._load_data(self.default)

    def apply(self):
        core_object.set_brightness(self.brightness)
    
    def _get_data(self) -> SettingsDict:
        return {'Brightness' : self.brightness}

    def _load_data(self, data : SettingsDict) -> bool:
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        self.brightness = data['Brightness']
        return True

    @staticmethod
    def validate_data(data : SettingsDict) -> bool:
        if data is None: return False
        if data.get('Brightness', _missing) is _missing: return False
        return True
    
    @classmethod
    def set_default(cls, new_default : SettingsDict) -> bool:
        if not cls.validate_data(new_default): return False
        cls.default = new_default
        return True
    
def the_runtime_imports():
    global core_object
    from framework.core.core import core_object