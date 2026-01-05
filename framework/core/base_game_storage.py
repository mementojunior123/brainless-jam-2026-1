from sys import platform as PLATFORM
import json
import os
from typing import Any, TypedDict
from framework.utils.helpers import AnyJson

if PLATFORM == 'emscripten':
    from platform import window

class MockGameData(TypedDict):
    """This is the base class for the game data that needs to be stored."""
    pass

class BaseGameStorage:
    """This is the base class for game storage. It must be implemented in game_storage.py."""
    def __init__(self) -> None:
        """Variables are initialised here."""
        pass

    def reset(self):
        """Variables are set to their default values here."""
        pass
    
    def validate_data(self, data : MockGameData) -> bool:
        """Function that validates that the game data that was passed to it is valid."""
        if data is None: return False
        return True

    def _get_data(self) -> MockGameData:
        """Function that extracts the game data from the current storage object."""
        return {}

    def _load_data(self, data : MockGameData) -> bool:
        """Function that loads the passed game data into the current storage object."""
        if not self.validate_data(data):
            print('Data is invalid!')
            return False
        return True

    def load(self, is_web : bool = False) -> bool:
        """
        Function that loads the current game data from file or from web.
            is_web: True if we are currently in a web environnement, else False. 
        Returns --> A boolean that represents the success status of the function.
        """
        return self._load_from_file() if not is_web else self._load_from_web()
    
    def save(self, is_web : bool = False) -> None:
        """
        Function that saves the current game data to file or to web.
            is_web: True if we are currently in a web environnement, else False.
        """
        self._save_to_file() if not is_web else self._save_to_web()

    def _load_from_file(self, file_path : str = 'assets/data/game_info.json') -> bool:
        """
        Function that loads the current game data from a file.
            file_path: The location of the game data file to load from. Defaults to "assets/data/game_info.json".
        Returns --> A boolean that represents the success status of the function.
        """
        with open(file_path, 'r') as file:
            data = json.load(file)
        if data:
            return self._load_data(data)
        return False

    def _save_to_file(self, file_path : str = 'assets/data/game_info.json') -> None:
        """
        Function that saves the current game data to file.
            file_path: The location of the game data file to save to. Defaults to "assets/data/game_info.json".
        """
        data = self._get_data()
        with open(file_path, 'w') as file:
            json.dump(data, file)

    def _load_from_web(self) -> bool:
        """
        Function that loads the current game data from web.
        Returns --> A boolean that represents the success status of the function.
        """
        web_data = self.get_web('GameData')
        if web_data is not None:
            data = json.loads(web_data)
            if data is not None:
                return self._load_data(data)
        return False

    def _save_to_web(self) -> None:
        """
        Function that saves the current game data to web.
        """
        data = self._get_data()
        self.set_web('GameData', json.dumps(data))

    def get_web(self, key : str) -> str|None:
        """
        Utility function that gets a value located in localStorage.
            key: The name of the value to access.
        Returns --> The string representing the value if it exists, otherwise None.
        """
        return window.localStorage.getItem(key)

    def set_web(self, key : str, value : str):
        """
        Utility function that sets a value in localStorage.
            key: The name of the value to set.
            value: The value to set.
        """
        window.localStorage.setItem(key, str(value))