import pygame
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.helpers import rotate_around_pivot_accurate, ColorType
from framework.utils.pivot_2d import Pivot2D
from typing import Literal

class UiSpriteGroup:
    base_name : str = 'Group'
    def __init__(self, *args : tuple[UiSprite], serial : str = ''):
        self.tag : None = None
        self.elements : list[UiSprite] = [arg for arg in args]
        self.name : str = self.base_name + serial
        self.visible : bool = True
    
    def draw(self, display : pygame.Surface):
        for element in self.elements:
            element.draw(display)

    def __index__(self, index : int):
        return self.elements[index]

    @staticmethod
    def new_group() -> 'UiSpriteGroup':
        return UiSpriteGroup(serial='')