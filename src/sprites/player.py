import pygame
from typing import Generator
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript

class Player(Sprite):
    active_elements : list['Player'] = []
    inactive_elements : list['Player'] = []
    linked_classes : list['Sprite'] = [Sprite]

    animation_assets : dict[int, pygame.Surface] = {
        i : pygame.transform.scale_by(
            load_alpha_to_colorkey(f"assets/graphics/player/player-{i}.png", (0, 255, 0)), 2) 
            for i in range(8)
    }
    ACCEL_SPEED : float = 3.0
    FRICTION : float = 0.3
    MIN_VELOCITY : float = 0.1
    MAX_VELOCITY : float = 9
    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.animation_images : dict[int, pygame.Surface]
        self.animation_script : PlayerAnimationScript
        self.velocity : pygame.Vector2
        Player.inactive_elements.append(self)

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        element = cls.inactive_elements[0]

        element.animation_images = cls.animation_assets
        element.image = element.animation_images[0]
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.velocity = pygame.Vector2(0, 0)
        element.move_rect(position_anchor, position)
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.animation_script = PlayerAnimationScript()
        element.animation_script.initialize(core_object.game.game_timer.get_time, element, 0.25)

        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        self.animation_script.process_frame()
        self.update_movement(delta)

    def update_movement(self, delta : float):
        accel = self.calculate_acceleration()
        self.velocity *=  ((1 - self.FRICTION) ** delta) ** 0.5

        self.velocity += accel * 0.5 * delta
        self.position += self.velocity * delta
        self.velocity += accel * 0.5 * delta

        self.velocity *=  ((1 - self.FRICTION) ** delta) ** 0.5
        curr_speed : float = self.velocity.magnitude()
        if curr_speed < Player.MIN_VELOCITY:
            self.velocity = pygame.Vector2(0, 0)
        elif curr_speed > Player.MAX_VELOCITY:
            self.velocity.scale_to_length(Player.MAX_VELOCITY)
        self.restrict_to_screen()
    
    def restrict_to_screen(self):
        if self.rect.right > Player.display_size[0]:
            self.rect.right = Player.display_size[0]
            if self.velocity.x > 0: self.velocity.x = 0
        if self.rect.bottom > Player.display_size[1]:
            self.rect.bottom = Player.display_size[1]
        if self.rect.left < 0:
            self.rect.left = 0
            if self.velocity.x < 0: self.velocity.x = 0
        if self.rect.top < 0:
            self.rect.top = 0

    
    def calculate_acceleration(self) -> pygame.Vector2:
        pressed_keys = pygame.key.get_pressed()
        accel_total : pygame.Vector2 = pygame.Vector2(0, 0)
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            accel_total += pygame.Vector2(-Player.ACCEL_SPEED, 0)
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            accel_total += pygame.Vector2(Player.ACCEL_SPEED, 0)
        return accel_total

    def clean_instance(self):
        super().clean_instance()

class PlayerAnimationScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, player : Player, cycle_time : float):
        return super().initialize(time_source, player, cycle_time)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : None = None) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, player : Player, cycle_time : float) -> Generator[None, None, str]:
        animation_timer : Timer = Timer(-1, time_source)
        prev_index : int = 0
        yield
        while True:
            image_index : int = int((animation_timer.get_time() * 8) // cycle_time) % 8
            if image_index != prev_index:
                player.image = player.animation_images[image_index]
                player.mask = pygame.mask.from_surface(player.image)
                prev_index = image_index
            yield


for _ in range(1): Player()
Sprite.register_class(Player)
