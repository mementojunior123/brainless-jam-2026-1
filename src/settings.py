import json
import pygame
from typing import TypedDict, Any
from sys import platform as PLATFORM
from framework.utils.helpers import AnyJson
from framework.core.base_settings import BaseSettings, runtime_imports, MissingKeyClass, _missing, SettingException, BaseSettingsDict

if PLATFORM == 'emscripten':
    from platform import window

class SettingsDict(BaseSettingsDict):
    Brightness : int
    KeybindMoveLeft : int
    KeybindMoveRight : int
    KeybindShoot : int
    KeybindSpecialAttack : int
    KeybindDash : int
    KeybindPause : int
    PixelateGame : bool

DEFAULT_SETTINGS : SettingsDict = {
    "Brightness" : 0,
    "KeybindMoveLeft" : pygame.K_a,
    "KeybindMoveRight" : pygame.K_d,
    "KeybindShoot" : pygame.K_SPACE,
    "KeybindSpecialAttack" : pygame.K_f,
    "KeybindDash" : pygame.K_LSHIFT,
    "KeybindPause" : pygame.K_p,
    "PixelateGame" : False
}

class Settings(BaseSettings):
    default : SettingsDict = DEFAULT_SETTINGS

    def __init__(self) -> None:
        self.brightness : int = self.default['Brightness']
        self.keybind_move_left : int = self.default['KeybindMoveLeft']
        self.keybind_move_right : int = self.default['KeybindMoveRight']
        self.keybind_shoot : int = self.default['KeybindShoot']
        self.keybind_special_attack : int = self.default['KeybindSpecialAttack']
        self.keybind_dash : int = self.default['KeybindDash']
        self.keybind_pause : int = self.default['KeybindPause']
        self.pixelate_game : bool = self.default['PixelateGame']
    
    def reset(self):
        self._load_data(self.default)

    def apply(self):
        core_object.set_brightness(self.brightness)
        self.apply_pixelation()
    
    def apply_pixelation(self):
        """Apply pixelation setting (web only)."""
        if not core_object.is_web():
            return
        try:
            if PLATFORM == 'emscripten':
                if self.pixelate_game:
                    window.canvas.style.imageRendering = "pixelated"
                else:
                    window.canvas.style.imageRendering = ""
        except (AttributeError, NameError):
            # If window.canvas doesn't exist, silently fail
            pass
    
    def _get_data(self) -> SettingsDict:
        return {
            'Brightness' : self.brightness,
            'KeybindMoveLeft' : self.keybind_move_left,
            'KeybindMoveRight' : self.keybind_move_right,
            'KeybindShoot' : self.keybind_shoot,
            'KeybindSpecialAttack' : self.keybind_special_attack,
            'KeybindDash' : self.keybind_dash,
            'KeybindPause' : self.keybind_pause,
            'PixelateGame' : self.pixelate_game
        }

    def _load_data(self, data : SettingsDict) -> bool:
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        self.brightness = data.get('Brightness', self.default['Brightness'])
        self.keybind_move_left = data.get('KeybindMoveLeft', self.default['KeybindMoveLeft'])
        self.keybind_move_right = data.get('KeybindMoveRight', self.default['KeybindMoveRight'])
        self.keybind_shoot = data.get('KeybindShoot', self.default['KeybindShoot'])
        self.keybind_special_attack = data.get('KeybindSpecialAttack', self.default['KeybindSpecialAttack'])
        self.keybind_dash = data.get('KeybindDash', self.default['KeybindDash'])
        self.keybind_pause = data.get('KeybindPause', self.default['KeybindPause'])
        self.pixelate_game = data.get('PixelateGame', self.default['PixelateGame'])
        return True

    @staticmethod
    def validate_data(data : SettingsDict) -> bool:
        if data is None: return False
        # Allow missing keys for backwards compatibility
        return True
    
    @classmethod
    def set_default(cls, new_default : SettingsDict) -> bool:
        if not cls.validate_data(new_default): return False
        cls.default = new_default
        return True
    
def the_runtime_imports():
    global core_object
    from framework.core.core import core_object