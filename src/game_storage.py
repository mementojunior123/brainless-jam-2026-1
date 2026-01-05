"""This module is made to handle saving game data on multiple platforms."""

from sys import platform as PLATFORM
import json
import os
from typing import Any, TypedDict
from framework.utils.helpers import AnyJson
from framework.core.base_game_storage import BaseGameStorage, MockGameData

if PLATFORM == 'emscripten':
    from platform import window

class GameData(MockGameData):
    """
    A TypedDict that defines the data that is stored in the game storage.
    """
    high_score : int

class GameStorage(BaseGameStorage):
    """
    Implementation of BaseGameStorage.
    """
    def __init__(self) -> None:
        """Constructor that initialises all of the data."""
        self.high_score : int = 0

    def reset(self):
        """
        Resets the data to its default value.
        """
        self.high_score = 0
    
    def validate_data(self, data : GameData) -> bool:
        """
        Function that verifies if data is valid game data.
            data: The data to verifiy.
        Returns --> True if the data is valid, else False.
        """
        if data is None: return False
        if not isinstance(data.get("high_score", None), int):
            return False
        return True

    def _get_data(self) -> GameData:
        """
        Function that converts the game storage object to a dictonnary that contains the data.
        Returns --> A GameData object (TypedDict).
        """
        return {'high_score' : self.high_score}

    def _load_data(self, data : GameData) -> bool:
        """
        Function that loads game data into the storage object.
            data: The data to load.
        Returns --> True on success, else False.
        """
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        self.high_score = data['high_score']
        return True