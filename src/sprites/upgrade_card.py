import pygame
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, ColorType
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
from framework.utils.my_timer import Timer, TimeSource
from typing import Generator
import framework.utils.interpolation as interpolation
from framework.utils.ui.textsprite import TextSprite
from src.sprites.projectiles import BaseProjectile, Teams

CARD_DIMENSIONS : int = (280, 350)

class UpgradeCard(Sprite):
    active_elements : list['UpgradeCard'] = []
    inactive_elements : list['UpgradeCard'] = []
    linked_classes : list['Sprite'] = [Sprite]

    default_image : pygame.Surface = pygame.surface.Surface(CARD_DIMENSIONS)
    default_image.fill((150, 150, 150))
    pygame.draw.rect(default_image, (130,160,210), default_image.get_rect(), width=10)
    default_image.set_colorkey((0, 255, 255))
    BACKGROUND_SPEED : float = 2
    SPAWN_BACKGROUND : bool = True
    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.current_script : CoroutineScript|None
        UpgradeCard.inactive_elements.append(self)

    @staticmethod
    def get_font(size : int) -> pygame.Font:
        return pygame.Font('assets/fonts/Pixeltype.ttf', size)

    @classmethod
    def spawn(cls, x_pos : int, text_lines : list[tuple[str, int, int|str, ColorType]]) -> "UpgradeCard":
        """
        text_tuple is a tuple of the text, y_level (relative to card.top), size
        """
        element = cls.inactive_elements[0]

        element.image = cls.default_image.copy()
        available_fonts : dict[str|int, pygame.Font] = {
            20 : core_object.game.font_20,
            25 : core_object.game.font_25,
            28 : core_object.game.font_28,
            30 : core_object.game.font_30,
            40 : core_object.game.font_40,
            50 : core_object.game.font_50,
            60 : core_object.game.font_60,
            70 : core_object.game.font_70,
            'small' : core_object.game.font_40,
            'huge' : core_object.menu.font_150,
            150 : core_object.menu.font_150
        }
        card_width : int = element.image.get_size()[0]
        for text_tuple in text_lines:
            text, y_level, size, text_color = text_tuple
            font_used = available_fonts.get(size, None) or UpgradeCard.get_font(size)
            text_stroke_size = 0 if text_color == "White" else 0
            text_image : pygame.Surface = TextSprite((0, 0), 'center', -1, text, text_settings=(font_used, text_color, False),
                                                  text_stroke_settings=('Black', text_stroke_size), colorkey=(0, 255, 255)).surf
            element.image.blit(text_image, text_image.get_rect(center=(card_width // 2, y_level)))
            
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect("midbottom", pygame.Vector2(x_pos, -200))
        element.zindex = 0
        element.current_camera = core_object.game.main_camera
        element.current_script = TransitionInScript()
        element.current_script.initialize(core_object.game.game_timer.get_time, element)
        cls.unpool(element)
        return element

    def update(self, delta: float):
        if self.current_script is not None:
            result = self.current_script.process_frame(delta)
            if result == 'DestroyCard':
                self.kill_instance_safe()
                return
            if self.current_script.is_over:
                self.current_script = None
    
    def check_collisions(self) -> bool:
        for proj in self.get_all_rect_colliding(BaseProjectile):
            if proj.team == Teams.ALLIED:
                return True
        return False
    
    def when_picked(self):
        self.current_script = WhenPickedScript()
        self.current_script.initialize(core_object.game.game_timer.get_time, self)
    
    def when_not_picked(self):
        self.current_script = TransitionOutScript()
        self.current_script.initialize(core_object.game.game_timer.get_time, self)

    
    def clean_instance(self):
        super().clean_instance()
        

for _ in range(5): UpgradeCard()
Sprite.register_class(UpgradeCard)

class TransitionInScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, card : UpgradeCard):
        return super().initialize(time_source, card)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, card : UpgradeCard) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        target_position : pygame.Vector2 = pygame.Vector2(card.position.x, centery - 50)
        start_position : pygame.Vector2 = card.position.copy()
        transition_timer : Timer = Timer(2, time_source)

        delta : float = yield
        if delta is None: delta = core_object.dt

        while not transition_timer.isover():
            alpha : float = interpolation.quad_ease_out(transition_timer.get_time() / transition_timer.duration)
            card.position = start_position.lerp(target_position, alpha)
            delta = yield
        card.position = target_position
        return "Done"

class WhenPickedScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, card : UpgradeCard):
        return super().initialize(time_source, card)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, card : UpgradeCard) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        target_position : pygame.Vector2 = pygame.Vector2(card.position.x, screen_sizey + 100 + card.image.get_size()[1] // 2)
        start_position : pygame.Vector2 = card.position.copy()
        transition_timer : Timer = Timer(1.5, time_source)

        delta : float = yield
        if delta is None: delta = core_object.dt

        while not transition_timer.isover():
            alpha : float = interpolation.smoothstep(transition_timer.get_time() / transition_timer.duration)
            card.position = start_position.lerp(target_position, alpha)
            card_alpha : float = pygame.math.lerp(255, 0, alpha * 1.5, True)
            card.image.set_alpha(card_alpha)
            delta = yield
        card.position = target_position
        return "DestroyCard"

class TransitionOutScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, card : UpgradeCard):
        return super().initialize(time_source, card)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, card : UpgradeCard) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        target_position : pygame.Vector2 = pygame.Vector2(card.position.x, -200 - card.image.get_size()[1] // 2)
        start_position : pygame.Vector2 = card.position.copy()
        transition_timer : Timer = Timer(1.5, time_source)

        delta : float = yield
        if delta is None: delta = core_object.dt

        while not transition_timer.isover():
            alpha : float = interpolation.quad_ease_in(transition_timer.get_time() / transition_timer.duration)
            card.position = start_position.lerp(target_position, alpha)
            delta = yield
        card.position = target_position
        return "DestroyCard"