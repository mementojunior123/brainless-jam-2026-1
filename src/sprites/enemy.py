import pygame
from typing import Generator
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript

class BaseEnemy(Sprite):
    active_elements : list['BaseEnemy'] = []
    inactive_elements : list['BaseEnemy'] = []
    linked_classes : list['Sprite'] = [Sprite]

    default_image : pygame.Surface = pygame.transform.rotate(
        load_alpha_to_colorkey("assets/graphics/enemy/enemy_v1-1.png", (0, 255, 0)),
        180)
    default_image2 : pygame.Surface = load_alpha_to_colorkey("assets/graphics/enemy/alien.png", (0, 255, 0))
    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.type : str
        self.health : float
        BaseEnemy.inactive_elements.append(self)

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot use BaseEnemy.spawn()")
        element = cls.inactive_elements[0]

        element.image = element.default_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        pass

    def clean_instance(self):
        super().clean_instance()
        self.type = None
        self.health = None

class BasicEnemy(BaseEnemy):
    active_elements : list['BasicEnemy'] = []
    inactive_elements : list['BasicEnemy'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseEnemy]
    BASE_SPEED : float = 5.0
    def __init__(self):
        super().__init__()
        self.control_script : BasicEnemyControlScript
        self.speed : float
        BasicEnemy.inactive_elements.append(self)
    
    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        element = cls.inactive_elements[0]

        element.image = BaseEnemy.default_image2
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.control_script = BasicEnemyControlScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element)
        element.speed = BasicEnemy.BASE_SPEED

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.control_script.process_frame(delta)
    
    def clean_instance(self):
        super().clean_instance()
        self.control_script = None
        self.speed = None

class BasicEnemyControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicEnemy):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicEnemy) -> Generator[None, float, str]: #Yield, Send, Return
        move_timer : Timer = Timer(-1, time_source)
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        direction : int = 1
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            unit.position += pygame.Vector2(direction * unit.speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            delta = yield

Sprite.register_class(BaseEnemy)
Sprite.register_class(BasicEnemy)
for _ in range(30): BasicEnemy()