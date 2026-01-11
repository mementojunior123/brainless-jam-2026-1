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

tip_list : list[str] = [
'''Dashing makes you invincible for a short period of time.\nTry to use it when you are cornered.''',
'''Dashing allows you to kill enemies that make it to the back row.\nUseful against runners (red enemies)!''',
'''Picking a new alternate fire does not reset
special attack and special firerate bonuses.
Weapon specialist upgrades, however, only apply to that specific weapon.'''
]
class TipUiGroup(UiSpriteGroup):
    base_name = 'TipUiGroup'
    def __init__(self, *args : tuple[UiSprite], serial : str = '', center : pygame.Vector2 = pygame.Vector2(480, 270)):
        super().__init__(*args, serial=serial)
        self.center = center
    
    @staticmethod
    def new_group(index : int = 0, alignment : str = 'midtop', position : pygame.Vector2|None = None) -> 'TipUiGroup':
        """Constructor for UiSpriteGroup."""
        position = position or pygame.Vector2(480, 100)
        elements = []
        for i, line in enumerate(tip_list[index].split('\n')):
            elements.append(TextSprite(position + pygame.Vector2(0, 40) * i, alignment, -1, line))
        return TipUiGroup(*elements, serial=f'')

            

class Menu(BaseMenu):
    """Implementation of the menu class."""
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    menu_theme : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/music/menu1_trimmed.ogg")
    menu_theme.set_volume(0.2)
    @staticmethod
    def _get_core_object():
        """Function that imports the core object at runtime."""
        global core_object
        from framework.core.core import core_object
        BaseMenu._get_core_object()
    
    def update_high_score(self):
        high_score_sprite : TextSprite = self.get_sprite_by_name(1, 'highscore_text')
        high_score_sprite.text = f'High score : {core_object.storage.high_score}'
        high_score_sprite.rect.midright = pygame.Vector2(960 - 15, 540 // 2)
    
    def prepare_entry(self, stage = 1):
        super().prepare_entry(stage)
        self.menu_theme.play()
        self.update_high_score()
    
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
        [BaseUiElements.new_text_sprite('Space Brawl', (Menu.font_60, 'Black', False), 0, 'midtop', (centerx, 50)),
        BaseUiElements.new_button('BlueButton', 'Play', 1, 'midbottom', (centerx, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'play_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_text_sprite('A/D or arrow keys to move', (Menu.font_50, 'Black', False), 0, 'midleft', (15, centery - 75)),
        BaseUiElements.new_text_sprite('Hold SPACE to shoot', (Menu.font_50, 'Black', False), 0, 'midleft', (15, centery - 25)),
        BaseUiElements.new_text_sprite('F for a special attack', (Menu.font_50, 'Black', False), 0, 'midleft', (15, centery + 25)),
        BaseUiElements.new_text_sprite('SHIFT to dash', (Menu.font_50, 'Black', False), 0, 'midleft', (15, centery + 75)),
        BaseUiElements.new_text_sprite('P to pause', (Menu.font_50, 'Black', False), 0, 'midleft', (15, centery + 125)),
        TextSprite(pygame.Vector2(window_size[0] - 15, centery), 'midright', 0,
        f'High score : {core_object.storage.high_score}', name='highscore_text', text_settings=(Menu.font_50, 'Black', False)),
        BaseUiElements.new_button('RedButton', 'Reset', 1, 'bottomleft', (15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'reset_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Help', 1, 'bottomright', (window_size[0] - 15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'help_button'}, (Menu.font_40, 'Black', False)),
        ],
        [
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 15), (0.5, 1.4), 
        {'name' : 'back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Next', 1, 'bottomright', (window_size[0] - 15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'next_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Prev', 1, 'bottomleft', (15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'prev_button'}, (Menu.font_40, 'Black', False)),
        TextSprite(pygame.Vector2(window_size[0] - 15, 15), 'topright', 0,
        f'1/{len(tip_list)}', name='tip_counter_text', text_settings=(Menu.font_50, 'Black', False)),
        ]
        ]
        self.bg_color = (94, 129, 162)
        self.add_connections()

    def enter_stage2(self):
        self.stage = 2
        sep : int = 4
        self.stage_data[2]['current_tip'] = 0
        self.stage_data[2]['max_tips'] = len(tip_list)
        self.stages[2].append(TipUiGroup.new_group(0))
        self.get_sprite_by_name(2, 'tip_counter_text').text = f'{1}/{len(tip_list)}'
    
    def change_tip_stage2(self, new_tip_index : int):
        self.stage_data[2]['current_tip'] = new_tip_index
        self.find_and_replace(TipUiGroup.new_group(new_tip_index), 2, name='TipUiGroup')
        self.get_sprite_by_name(2, 'tip_counter_text').text = f'{new_tip_index + 1}/{len(tip_list)}'
    
    def increment_tip_stage2(self):
        new_tip_index : int = (self.stage_data[2]['current_tip'] + 1) % self.stage_data[2]['max_tips']
        self.change_tip_stage2(new_tip_index)

    def decrement_tip_stage2(self):
        new_tip_index : int = (self.stage_data[2]['current_tip'] - 1) % self.stage_data[2]['max_tips']
        self.change_tip_stage2(new_tip_index)
    
    def exit_stage2(self):
        self.stage_data[2].clear()
        self.remove_sprite(2, name='TipUiGroup')
    
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
                elif name == 'reset_button':
                    core_object.storage.reset()
                    core_object.storage.save(core_object.is_web())
                    self.update_high_score()
                if name == 'help_button':
                    self.goto_stage(2)
            case 2:
                if name == 'back_button':
                    self.goto_stage(1)
                elif name == 'prev_button':
                    self.decrement_tip_stage2()
                elif name == 'next_button':
                    self.increment_tip_stage2()

# TODO : Document the menu API (general workflow, interactivity, etc.)