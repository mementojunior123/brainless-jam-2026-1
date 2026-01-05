import json
from typing import TypedDict, Any
from sys import platform as PLATFORM
from framework.utils.helpers import AnyJson

if PLATFORM == 'emscripten':
    from platform import window

class SettingException(BaseException):
    pass

class MissingKeyClass:
    def __init__(self):
        pass

_missing = MissingKeyClass()


class BaseSettingsDict(TypedDict):
    Brightness : int

DEFAULT_SETTINGS : BaseSettingsDict = {
    "Brightness" : 0
}

class BaseSettings:
    default : BaseSettingsDict = DEFAULT_SETTINGS

    def __init__(self) -> None:
        self.brightness : int = self.default['Brightness']
    
    def reset(self):
        self._load_data(self.default)

    def apply(self):
        core_object.set_brightness(self.brightness)
    
    def _get_data(self) -> BaseSettingsDict:
        return {'Brightness' : self.brightness}

    def _load_data(self, data : BaseSettingsDict) -> bool:
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        self.brightness = data['Brightness']
        return True

    @staticmethod
    def validate_data(data : BaseSettingsDict) -> bool:
        if data is None: return False
        if data.get('Brightness', _missing) is _missing: return False
        return True
    
    def load(self, is_web : bool = False) -> bool:
        return self._load_from_file() if not is_web else self._load_from_web()
    
    def save(self, is_web : bool = False) -> None:
        self._save_to_file() if not is_web else self._save_to_web()

    def _load_from_file(self, file_path : str = 'assets/data/settings.json') -> bool:
        with open(file_path, 'r') as file:
            data = json.load(file)
        if data:
            return self._load_data(data)
        return False

    def _save_to_file(self, file_path : str = 'assets/data/settings.json') -> None:
        data = self._get_data()
        with open(file_path, 'w') as file:
            json.dump(data, file)

    def _load_from_web(self) -> bool:
        web_data = self.get_web('SettingsData')
        if web_data is not None:
            data = json.loads(web_data)
            if data is not None:
                return self._load_data(data)
        return False

    def _save_to_web(self) -> None:
        data = self._get_data()
        self.set_web('SettingsData', json.dumps(data))

    def get_web(self, key : str) -> str:
        return window.localStorage.getItem(key)

    def set_web(self, key : str, value : Any):
        window.localStorage.setItem(key, str(value))

    @classmethod
    def set_default(cls, new_default : BaseSettingsDict) -> bool:
        if not cls.validate_data(new_default): return False
        cls.default = new_default
        return True
    
def runtime_imports():
    global core_object
    from framework.core.core import core_object