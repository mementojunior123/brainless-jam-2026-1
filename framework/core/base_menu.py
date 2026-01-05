import pygame
import random
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

class BaseMenu:
    """Base class for the menu."""
    font_40 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 40)
    font_50 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 50)
    font_60 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 60)
    font_70 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 70)
    font_150 = pygame.font.Font(r'assets/fonts/Pixeltype.ttf', 150)

    @staticmethod
    def _get_core_object():
        """Function that imports the core object at runtime."""
        global core_object
        from framework.core.core import core_object

    def __init__(self) -> None:
        """Constructor for the menu object that runs before runtime imports."""
        self.stage : int
        self.stages : list[list[UiSprite|UiSpriteGroup]|None]
        self.bg_color : ColorType|str
        self.temp : dict[UiSprite|UiSpriteGroup, Timer] = {}
        
    def init(self):
        """Initialises a menu object. Must be ran after runtime imports."""
        self.bg_color = (94, 129, 162)
        self.stage = 1
        self.stage_data : list[dict] = [None, {}]
        self.stages = [None, []]
    
    def add_temp(self, element : UiSprite|UiSpriteGroup, time : float|Timer, 
                 override = False, time_source : Callable[[], float]|None = None, time_scale : float = 1):
        """
        Function that adds an element to the menu temporarily.
            element: The ui element to add.
            time: The amount of time to add it for. Can also be a timer.
            override: If True and the element is already present temporarily, the timer for that element is overriden.
            time_source: The timestamp function to be used for this element's timer. Is optional.
            time_scale: The multiplicative factor that gets applied to the timestamp function of the element's timer. Is optional.
        """
        if element not in self.temp or override == True:
            timer = time if type(time) == Timer else Timer(time, time_source, time_scale)
            self.temp[element] = timer
    
    def alert_player(self, text : str, alert_speed : float = 1):
        """
        Function that shows a default alert message to the player.
            text: The text that will be shown by the alert.
            alert_speed: Applies a speedup (or slowdown) factor to the alert animation.
        """
        text_sprite = TextSprite(pygame.Vector2(core_object.main_display.get_width() // 2, 90), 'midtop', 0, text, 
                        text_settings=(core_object.menu.font_60, 'White', False), text_stroke_settings=('Black', 2), colorkey=(0,255,0))
        
        text_sprite.rect.bottom = -5
        text_sprite.position = pygame.Vector2(text_sprite.rect.center)
        temp_y = text_sprite.rect.centery
        self.add_temp(text_sprite, 5)
        TInfo = TweenModule.TweenInfo
        goal1 = {'rect.centery' : 50, 'position.y' : 50}
        info1 = TInfo(interpolation.quad_ease_out, 0.3 / alert_speed)
        goal2 = {'rect.centery' : temp_y, 'position.y' : temp_y}
        info2 = TInfo(interpolation.quad_ease_in, 0.4 / alert_speed)
        
        on_screen_time = 1 / alert_speed
        info_wait = TInfo(lambda t : t, on_screen_time)
        goal_wait = {}

        chain = TweenModule.TweenChain(text_sprite, [(info1, goal1), (info_wait, goal_wait), (info2, goal2)], True)
        chain.register()
        chain.play()

    def add_connections(self):
        """
        Function that binds relevant events to their menu object callbacks.
        """
        core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.bind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    def remove_connections(self):
        """
        Function that unbinds relevant events from their menu object callbacks.
        """
        core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, self.handle_mouse_event)
        core_object.event_manager.unbind(UiSprite.TAG_EVENT, self.handle_tag_event)
    
    

    def render(self, display : pygame.Surface):
        """
        Function that renders the menu object.
            display: The surface where the menu gets rendered.
        """
        sprite_list : list[UiSprite] = []
        for sprite in (self.stages[self.stage] + list(self.temp.keys())):
            if isinstance(sprite, UiSpriteGroup):
                sprite_list += sprite.elements
            else:
                sprite_list.append(sprite)
        sprite_list.sort(key = lambda sprite : sprite.zindex)
        for sprite in filter(lambda sprite : sprite.visible, sprite_list):
            sprite.draw(display)
        
    
    def update(self, delta : float):
        """
        Function that runs every frame, allowing frame-based updates to happen.
            delta: The current delta factor. See core.py for more details on delta's functionement.
        """
        to_del = []
        for item in self.temp:
            if self.temp[item].isover(): to_del.append(item)
        for item in to_del:
            self.temp.pop(item)
    
    def prepare_entry(self, stage : int = 1):
        """
        Function that runs right before the menu is entered (but not on startup).
            stage: The stage that will be entered.
        """
        self.add_connections()
        self.stage = stage
    
    def prepare_exit(self):
        """
        Function that runs right before the menu is exited.
        """
        self.stage = 0
        self.remove_connections()
        self.temp.clear()
    
    def goto_stage(self, new_stage : int):
        """
        Function that exits the current stage then enters a stage.
            new_stage: The stage to enter.
        """
        self.exit_stage()
        self.enter_stage(new_stage)

    def enter_stage(self, new_stage : int):
        """
        Function that enters a new stage. Automatically uses enter_stage_[stage_number] if it exists. Otherwise, it does nothing.
            new_stage: The stage to enter.
        """
        entry_funcion = getattr(self, f'enter_stage{new_stage}', noop)
        entry_funcion()
        self.stage = new_stage
    
    def exit_stage(self):
        """
        Function that exits the current stage. Automatically uses exit_stage_[stage_number] if it exists. Otherwise, it does nothing.
        """
        exit_funcion = getattr(self, f'exit_stage{self.stage}', noop)
        exit_funcion()

    def get_sprite(self, stage : int, tag : int) -> UiSprite|None:
        """
        Function that searches a stage for a sprite with a given tag, and returns the first sprite found.
            stage: The stage to search.
            tag: The sprite's tag attribute to look for.
        Returns --> A sprite if it was found, otherwise None.
        """
        if tag is None or stage is None: return None

        the_list : list[UiSprite|UiSpriteGroup] = self.stages[stage]
        for sprite in the_list:
            if sprite.tag == tag:
                return sprite
        return None
    
    def get_sprite_by_name(self, stage : int, name : str) -> UiSprite|UiSpriteGroup|None:
        """
        Function that searches a stage for a sprite with a given name, and returns the first sprite found.
            stage: The stage to search.
            name: The sprite's name attribute to look for.
        Returns --> A sprite or sprite group if it was found, otherwise None.
        """
        if name is None or stage is None: return None

        the_list = self.stages[stage]
        sprite : UiSprite|UiSpriteGroup
        for sprite in the_list:
            if sprite.name == name:
                return sprite
        return None

    def get_sprite_index(self, stage : int, name : str|None = None, tag : int|None = None) -> int|None:
        """
        Function that searches a stage for a sprite with a given name or tag, and returns the index of the first sprite that matches any condition.
            stage: The stage to search.
            tag: The sprite's tag attribute to look for.
            name: The sprite's name attribute to look for.
        Returns --> The index of the sprite if it was found, otherwise None.
        ***
        No search criteria (name or tag) is obligatory, but alteast one must be given.
        """
        if (name is None and tag is None) or stage is None: return None
        the_list = self.stages[stage]
        sprite : UiSprite|UiSpriteGroup
        for i, sprite in enumerate(the_list):
            if sprite.name == name and name is not None:
                return i
            if sprite.tag == tag and tag is not None:
                return i
        return None
    
    def find_and_replace(self, new_sprite : UiSprite|UiSpriteGroup, stage : int, name : str|None = None, 
                         tag : int|None = None, old_sprite : UiSprite|UiSpriteGroup|None = None) -> bool:
        """
        Function that looks for a given sprite, name or tag and replaces the first occurence with a new sprite.
            new_sprite: The new sprite or sprite group.
            stage: The stage index to search.
            name: The name of the sprite or sprite group to look for.
            tag: The tag to look for.
            old_sprite: The sprite or sprite group to look for.
        Returns --> A boolean that represents the success of the operation.
        ***
        Only one of the 3 criteria (old_sprite, tag, name) has to match.
        No search criteria is obligatory, but alteast one must be given.
        """
        found : bool = False
        for index, sprite in enumerate(self.stages[stage]):
            if sprite == old_sprite and old_sprite is not None:
                found = True
                break
            if sprite.tag == tag and tag is not None:
                found = True
                break
            if sprite.name == name and name is not None:
                found = True
                break
        
        if found:
            self.stages[stage][index] = new_sprite
        else:
            print('Find and replace failed')
        return found
    
    def remove_sprite(self, stage : int, sprite : UiSprite|UiSpriteGroup|None = None, 
                      name : str|None = None, tag : int|None = None) -> None|UiSpriteGroup|UiSpriteGroup:
        """
        Function that looks for a given sprite, name or tag and removes the first occurence.
            stage: The stage index to search.
            name: The name of the sprite or sprite group to look for.
            tag: The tag to look for.
            old_sprite: The sprite or sprite group to look for.
        Returns --> The removed sprite or sprite group.
        ***
        Only one of the 3 criteria (old_sprite, tag, name) has to match.
        No search criteria is obligatory, but alteast one must be given.
        """
        if sprite is None and name is None and tag is None: return None
        found : UiSprite|UiSpriteGroup|None = None
        for index, element in enumerate(self.stages[stage]):
            if element is None: continue
            if element == sprite and sprite is not None:
                found = element
                break
            if element.tag == tag and tag is not None:
                found = element
                break
            if element.name == name and name is not None:
                found = element
                break
        
        if found:
            self.stages[stage].remove(found)
        else:
            print('Removal failed')
        return found

    def handle_tag_event(self, event : pygame.Event):
        """
        Default event handler for tag events. See UiSprite for more details on tag events.
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
                pass
                   
    
    def handle_mouse_event(self, event : pygame.Event):
        """
        Default event handler for mouse events.
            event: The event to handle.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos : tuple = event.pos
            sprite : UiSprite|UiSpriteGroup
            for sprite in self.stages[self.stage]:
                if type(sprite) == UiSprite:
                    if sprite.rect.collidepoint(mouse_pos):
                        sprite.on_click()
                elif type(sprite) == UiSpriteGroup:
                    for real_sprite in sprite.elements:
                        if real_sprite.rect.collidepoint(mouse_pos):
                            real_sprite.on_click()