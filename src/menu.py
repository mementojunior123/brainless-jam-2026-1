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
    font_30 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 30)
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
        
        self.stage_data : list[dict] = [None, {}, {}, {}, {}, {}]  # Stage 0 (unused), 1 (main), 2 (help), 3 (keybinds), 4 (settings submenu), 5 (graphics)
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
        BaseUiElements.new_button('GreenButton', 'Settings', 1, 'midbottom', (centerx, centery + 100), (0.5, 1.4), 
        {'name' : 'settings_button'}, (Menu.font_40, 'Black', False)),
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
        ],
        [
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 15), (0.5, 1.4), 
        {'name' : 'keybind_back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Defaults', 1, 'bottomright', (window_size[0] - 15, window_size[1] - 15), (0.5, 1.4), 
        {'name' : 'keybind_reset_button'}, (Menu.font_40, 'Black', False)),
        ],
        [
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 15), (0.5, 1.4), 
        {'name' : 'settings_back_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Keybinds', 1, 'midtop', (centerx, centery - 50), (0.5, 1.4), 
        {'name' : 'settings_keybinds_button'}, (Menu.font_40, 'Black', False)),
        BaseUiElements.new_button('BlueButton', 'Graphics', 1, 'midtop', (centerx, centery + 50), (0.5, 1.4), 
        {'name' : 'settings_graphics_button'}, (Menu.font_40, 'Black', False)),
        ],
        [
        BaseUiElements.new_button('BlueButton', 'Back', 1, 'topleft', (15, 15), (0.5, 1.4), 
        {'name' : 'graphics_back_button'}, (Menu.font_40, 'Black', False)),
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
    
    def enter_stage3(self):
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2
        centery = window_size[1] // 2
        
        # Initialize stage data if needed
        if len(self.stage_data) <= 3:
            self.stage_data.append({})
        self.stage_data[3]['rebinding'] = None
        self.stage_data[3]['keybind_buttons'] = {}
        self.stage_data[3]['keybind_texts'] = {}
        
        # Clear any existing keybind UI
        for name in ['keybind_move_left_button', 'keybind_move_right_button', 'keybind_shoot_button', 
                     'keybind_special_attack_button', 'keybind_dash_button', 'keybind_pause_button',
                     'keybind_move_left_text', 'keybind_move_right_text', 'keybind_shoot_text',
                     'keybind_special_attack_text', 'keybind_dash_text', 'keybind_pause_text',
                     'keybind_move_left_label', 'keybind_move_right_label', 'keybind_shoot_label',
                     'keybind_special_attack_label', 'keybind_dash_label', 'keybind_pause_label']:
            self.remove_sprite(3, name=name)
        
        # Create keybind UI elements with more spacing, centered vertically
        # Total height: 6 items * 60px spacing = 360px, so start at centery - 180
        keybind_configs = [
            ('move_left', 'Move Left', pygame.Vector2(centerx, centery - 140)),
            ('move_right', 'Move Right', pygame.Vector2(centerx, centery - 80)),
            ('shoot', 'Shoot', pygame.Vector2(centerx, centery - 20)),
            ('special_attack', 'Special Attack', pygame.Vector2(centerx, centery + 40)),
            ('dash', 'Dash', pygame.Vector2(centerx, centery + 100)),
            ('pause', 'Pause', pygame.Vector2(centerx, centery + 160)),
        ]
        
        for action, label, pos in keybind_configs:
            # Label text
            label_text = TextSprite(pos + pygame.Vector2(-150, 0), 'midright', 0, label + ':', 
                                   f'keybind_{action}_label', text_settings=(Menu.font_40, 'Black', False))
            self.stages[3].append(label_text)
            
            # Current keybind text
            key_name = self.get_key_name(core_object.settings.__getattribute__(f'keybind_{action}'))
            key_text = TextSprite(pos + pygame.Vector2(-100, 0), 'midleft', 0, key_name, 
                                 f'keybind_{action}_text', text_settings=(Menu.font_40, 'Black', False))
            self.stages[3].append(key_text)
            self.stage_data[3]['keybind_texts'][action] = key_text
            
            # Rebind button
            button = BaseUiElements.new_button('BlueButton', 'Rebind', 1, 'midleft', 
                                              pos + pygame.Vector2(120, 0), (0.5, 1.2), 
                                              {'name' : f'keybind_{action}_button'}, (Menu.font_40, 'Black', False))
            self.stages[3].append(button)
            self.stage_data[3]['keybind_buttons'][action] = button
        
        self.stage = 3
    
    def exit_stage3(self):
        self.stage_data[3].clear()
        # Remove all keybind UI elements
        for name in ['keybind_move_left_button', 'keybind_move_right_button', 'keybind_shoot_button', 
                     'keybind_special_attack_button', 'keybind_dash_button', 'keybind_pause_button',
                     'keybind_move_left_text', 'keybind_move_right_text', 'keybind_shoot_text',
                     'keybind_special_attack_text', 'keybind_dash_text', 'keybind_pause_text',
                     'keybind_move_left_label', 'keybind_move_right_label', 'keybind_shoot_label',
                     'keybind_special_attack_label', 'keybind_dash_label', 'keybind_pause_label']:
            self.remove_sprite(3, name=name)
    
    def enter_stage5(self):
        window_size = core_object.main_display.get_size()
        centerx = window_size[0] // 2
        centery = window_size[1] // 2
        
        # Initialize stage data if needed
        if len(self.stage_data) <= 5:
            self.stage_data.append({})
        
        # Clear any existing graphics UI
        for name in ['graphics_pixelate_label', 'graphics_pixelate_checkbox', 'graphics_pixelate_status']:
            self.remove_sprite(5, name=name)
        
        # Label
        label_text = TextSprite(pygame.Vector2(centerx, centery - 50), 'center', 0, 
                               'Pixelate Game (BROWSER ONLY):', 
                               'graphics_pixelate_label', 
                               text_settings=(Menu.font_40, 'Black', False))
        self.stages[5].append(label_text)
        
        # Checkbox button (toggle)
        checkbox_state = core_object.settings.pixelate_game
        button_type = 'GreenButton' if checkbox_state else 'RedButton'
        button_text = 'ON' if checkbox_state else 'OFF'
        checkbox_button = BaseUiElements.new_button(button_type, button_text, 1, 'center', 
                                                    (centerx, centery), (0.5, 1.4), 
                                                    {'name' : 'graphics_pixelate_checkbox'}, 
                                                    (Menu.font_40, 'Black', False))
        self.stages[5].append(checkbox_button)
        self.stage_data[5]['checkbox_button'] = checkbox_button
        
        # Status text (only show if not web)
        if not core_object.is_web():
            status_text = TextSprite(pygame.Vector2(centerx, centery + 50), 'center', 0, 
                                    '(Not available in desktop version)', 
                                    'graphics_pixelate_status', 
                                    text_settings=(Menu.font_30, 'Gray', False))
            self.stages[5].append(status_text)
        
        self.stage = 5
    
    def exit_stage5(self):
        self.stage_data[5].clear()
        # Remove all graphics UI elements
        for name in ['graphics_pixelate_label', 'graphics_pixelate_checkbox', 'graphics_pixelate_status']:
            self.remove_sprite(5, name=name)
    
    def toggle_pixelation(self):
        """Toggle pixelation setting."""
        if not core_object.is_web():
            return  # Don't do anything if not in web context
        
        # Toggle the setting
        core_object.settings.pixelate_game = not core_object.settings.pixelate_game
        core_object.settings.save(core_object.is_web())
        core_object.settings.apply_pixelation()
        
        # Update the checkbox button
        checkbox_button = self.stage_data[5].get('checkbox_button')
        if checkbox_button:
            button_type = 'GreenButton' if core_object.settings.pixelate_game else 'RedButton'
            button_text = 'ON' if core_object.settings.pixelate_game else 'OFF'
            # Recreate the button with new state
            window_size = core_object.main_display.get_size()
            centerx = window_size[0] // 2
            centery = window_size[1] // 2
            new_button = BaseUiElements.new_button(button_type, button_text, 1, 'center', 
                                                  (centerx, centery), (0.5, 1.4), 
                                                  {'name' : 'graphics_pixelate_checkbox'}, 
                                                  (Menu.font_40, 'Black', False))
            self.find_and_replace(new_button, 5, name='graphics_pixelate_checkbox')
            self.stage_data[5]['checkbox_button'] = new_button
    
    def get_key_name(self, key_code : int) -> str:
        """Convert a pygame key code or mouse button to a readable name."""
        # Mouse buttons (pygame uses 1-5 for mouse buttons)
        if key_code == 1 or key_code == pygame.BUTTON_LEFT:
            return 'Mouse Left'
        elif key_code == 3 or key_code == pygame.BUTTON_RIGHT:
            return 'Mouse Right'
        elif key_code == 2 or key_code == pygame.BUTTON_MIDDLE:
            return 'Mouse Middle'
        elif key_code == 4 or key_code == pygame.BUTTON_X1:
            return 'Mouse X1'
        elif key_code == 5 or key_code == pygame.BUTTON_X2:
            return 'Mouse X2'
        
        # Keyboard keys
        key_name = pygame.key.name(key_code)
        if key_name:
            return key_name.replace('left ', 'L').replace('right ', 'R').title()
        return f'Key {key_code}'
    
    def start_keybind_rebinding(self, action_name : str):
        """Start listening for a new keybind for the given action."""
        self.stage_data[3]['rebinding'] = action_name
        # Update the button text to show we're waiting for input
        button = self.stage_data[3]['keybind_buttons'].get(action_name)
        if button:
            # We'll need to update the button text, but since it's a UiSprite, we'll use a text sprite overlay
            text_sprite = self.stage_data[3]['keybind_texts'].get(action_name)
            if text_sprite:
                text_sprite.text = 'Press any key...'
    
    def apply_keybind(self, action_name : str, key_code : int):
        """Apply a new keybind for the given action."""
        # Map action names to settings attributes
        action_map = {
            'move_left': 'keybind_move_left',
            'move_right': 'keybind_move_right',
            'shoot': 'keybind_shoot',
            'special_attack': 'keybind_special_attack',
            'dash': 'keybind_dash',
            'pause': 'keybind_pause'
        }
        
        if action_name in action_map:
            attr_name = action_map[action_name]
            setattr(core_object.settings, attr_name, key_code)
            core_object.settings.save(core_object.is_web())
            
            # Update the display
            text_sprite = self.stage_data[3]['keybind_texts'].get(action_name)
            if text_sprite:
                text_sprite.text = self.get_key_name(key_code)
            
            self.stage_data[3]['rebinding'] = None
    
    def reset_keybinds_to_defaults(self):
        """Reset all keybinds to their default values."""
        import pygame
        defaults = {
            'move_left': pygame.K_a,
            'move_right': pygame.K_d,
            'shoot': pygame.K_SPACE,
            'special_attack': pygame.K_f,
            'dash': pygame.K_LSHIFT,
            'pause': pygame.K_p
        }
        
        for action_name, key_code in defaults.items():
            self.apply_keybind(action_name, key_code)
    
    def add_connections(self):
        """Function that binds relevant events to their menu object callbacks."""
        super().add_connections()
        core_object.event_manager.bind(pygame.KEYDOWN, self.handle_key_event)
    
    def remove_connections(self):
        """Function that unbinds relevant events from their menu object callbacks."""
        super().remove_connections()
        core_object.event_manager.unbind(pygame.KEYDOWN, self.handle_key_event)
    
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
                elif name == 'settings_button':
                    self.goto_stage(4)
            case 2:
                if name == 'back_button':
                    self.goto_stage(1)
                elif name == 'prev_button':
                    self.decrement_tip_stage2()
                elif name == 'next_button':
                    self.increment_tip_stage2()
            case 3:
                if name == 'keybind_back_button':
                    self.goto_stage(4)
                elif name == 'keybind_reset_button':
                    self.reset_keybinds_to_defaults()
                elif name and name.startswith('keybind_') and name.endswith('_button'):
                    # Extract the action name from the button name
                    action_name = name.replace('keybind_', '').replace('_button', '')
                    if action_name in ['move_left', 'move_right', 'shoot', 'special_attack', 'dash', 'pause']:
                        self.start_keybind_rebinding(action_name)
            case 4:
                if name == 'settings_back_button':
                    self.goto_stage(1)
                elif name == 'settings_keybinds_button':
                    self.goto_stage(3)
                elif name == 'settings_graphics_button':
                    self.goto_stage(5)
            case 5:
                if name == 'graphics_back_button':
                    self.goto_stage(4)
                elif name == 'graphics_pixelate_checkbox':
                    self.toggle_pixelation()
    
    def handle_key_event(self, event : pygame.Event):
        """Handle keyboard events for keybind rebinding."""
        if self.stage == 3 and self.stage_data[3].get('rebinding'):
            if event.type == pygame.KEYDOWN:
                action_name = self.stage_data[3]['rebinding']
                self.apply_keybind(action_name, event.key)
    
    def handle_mouse_event(self, event : pygame.Event):
        """Handle mouse events for keybind rebinding and menu interaction."""
        # First handle rebinding
        if self.stage == 3 and self.stage_data[3].get('rebinding'):
            if event.type == pygame.MOUSEBUTTONDOWN:
                action_name = self.stage_data[3]['rebinding']
                # pygame.MOUSEBUTTONDOWN uses button numbers 1-5 directly
                self.apply_keybind(action_name, event.button)
                return  # Don't process as menu click
        
        # Then handle normal menu interaction
        super().handle_mouse_event(event)

# TODO : Document the menu API (general workflow, interactivity, etc.)