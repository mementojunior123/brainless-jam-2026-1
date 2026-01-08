import pygame
import random
from framework.core.base_menu import BaseMenu
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.ui.ui_sprite_group import UiSpriteGroup
from framework.utils.ui.textsprite import TextSprite
from framework.utils.ui.base_ui_elements import BaseUiElements
import framework.utils.tween_module as TweenModule
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer
from framework.utils.ui.brightness_overlay import BrightnessOverlay
from math import floor, ceil
from framework.utils.helpers import ColorType
from typing import Callable

def noop():
    pass

test_list : list[str] = ['up', 'right', 'showdown', 'critical', 'double-up', 'switch', 'fake-run', 'remontada']
class TestUiGroup(UiSpriteGroup):
    """A demonstration of UiSpriteGroup."""
    base_name = 'TestGroup'
    def __init__(self, *args : tuple[UiSprite], serial : str = '', center : pygame.Vector2 = pygame.Vector2(480, 270)):
        super().__init__(*args, serial=serial)
        self.center = center
    
    @staticmethod
    def new_group(page : int, sep : int = 4, center = pygame.Vector2(480, 270)) -> 'TestUiGroup':
        """Constructor for UiSpriteGroup."""
        start_index : int = sep * page
        end_index : int = sep * (page + 1)
        name_amount : int = len(test_list)
        if start_index >= name_amount:
            raise ValueError('Page does not exist')
        if end_index > name_amount: end_index = name_amount
        name_list : list[str] = test_list[start_index: end_index]
        elements : list[TextSprite] = []
        aligments = [(pygame.Vector2(-200, -200), 'topleft'), (pygame.Vector2(200, -200), 'topright'), 
                     (pygame.Vector2(-200, 200), 'bottomleft'),(pygame.Vector2(200, 200), 'bottomright')]
        for text, aligment in zip(name_list, aligments):
            new_sprite = TextSprite(center + aligment[0], aligment[1], 0, text, None, text_settings=(BaseMenu.font_50, 'White', False),
                                    text_stroke_settings=('Black', 2), colorkey=(0, 255, 0))
            elements.append(new_sprite)
        return TestUiGroup(*elements, serial=f'')

            

class Menu(BaseMenu):
    """Implementation of the menu class."""
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    menu_theme : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/music/menu1.ogg")
    menu_theme.set_volume(0.3)
    @staticmethod
    def _get_core_object():
        """Function that imports the core object at runtime."""
        global core_object
        from framework.core.core import core_object
        BaseMenu._get_core_object()
    
    def prepare_entry(self, stage = 1):
        super().prepare_entry(stage)
        self.menu_theme.play()
    
    def init(self):
        """Initialises a menu object. Must be ran after runtime imports."""
        self._get_core_object()
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2
        centery = window_size[1] // 2
        wx, wy = window_size

        self.stage = 1
        
        self.stage_data : list[dict] = [None, {}, {}]
        self.stages = [None, 
        [BaseUiElements.new_text_sprite('Game Title', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (centerx, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'play_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Test', 1, 'bottomright', (wx - 15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'test_button'}, (Menu.font_40, 'Black', False))], #stage 1

        [BaseUiElements.new_button('BlueButton', 'Prev', 1, 'bottomleft', (20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 2, 'bottomright', (wx - 20, window_size[1] - 25), (0.4, 1.0), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Back', 3, 'topleft', (15, 15), (0.4, 1.0), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),]
        ]
        self.bg_color = (94, 129, 162)
        self.add_connections()   

    def enter_stage2(self):
        self.stage = 2
        sep : int = 4
        self.stage_data[2]['current_page'] = 0
        self.stage_data[2]['max_pages'] = ceil(len(test_list) / sep)
        self.stages[2].append(TestUiGroup.new_group(0))
    
    def change_page_stage2(self, new_page : int):
        self.stage_data[2]['current_page'] = new_page
        self.find_and_replace(TestUiGroup.new_group(new_page), 2, name='TestGroup')
    
    def increment_page_stage2(self):
        new_page : int = (self.stage_data[2]['current_page'] + 1) % self.stage_data[2]['max_pages']
        self.change_page_stage2(new_page)

    def decrement_page_stage2(self):
        new_page : int = (self.stage_data[2]['current_page'] - 1) % self.stage_data[2]['max_pages']
        self.change_page_stage2(new_page)
    
    def exit_stage2(self):
        self.stage_data[2].clear()
        self.remove_sprite(2, name='TestGroup')
    
    def update(self, delta : float):
        """
        Function that runs every frame, allowing frame-based updates to happen.
            delta: The current delta factor. See core.py for more details on delta's functionement.
        """
        super().update(delta)
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                pass
    
    def handle_tag_event(self, event : pygame.Event):
        """
        Event handler for tag events.
            event: The event to handle.
        """
        if event.type != UiSprite.TAG_EVENT:
            return
        tag : int = event.tag
        name : str = event.name
        trigger_type : str = event.trigger_type
        stage_data = self.stage_data[self.stage]
        match self.stage:
            case 1:
                if name == "play_button":
                    self.menu_theme.stop()
                    pygame.event.post(pygame.Event(core_object.START_GAME, {'mode' : 'test'}))
                if name == 'test_button':
                    self.goto_stage(2)
            case 2:
                if name == 'back_button':
                    self.goto_stage(1)
                elif name == 'prev_button':
                    self.decrement_page_stage2()
                elif name == 'next_button':
                    self.increment_page_stage2()

# TODO : Document the menu API (general workflow, interactivity, etc.)