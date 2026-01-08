import pygame
from typing import Generator, TypeAlias, Literal
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
import src.sprites.projectiles
from src.sprites.projectiles import NormalProjectile, BaseProjectile, HomingProjectile, Teams
import src.sprites.enemy
from src.sprites.enemy import BaseEnemy
import random
from enum import Enum
from framework.utils.particle_effects import ParticleEffect
import framework.utils.interpolation as interpolation
from framework.utils.ui.ui_sprite import UiSprite

class BaseBoss(BaseEnemy):
    active_elements : list['BaseBoss'] = []
    inactive_elements : list['BaseBoss'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseEnemy]

    def __init__(self) -> None:
        super().__init__()
        BaseBoss.inactive_elements.append(self)

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")

class BaseMiniboss(BaseEnemy):
    active_elements : list['BaseMiniboss'] = []
    inactive_elements : list['BaseMiniboss'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseEnemy]

    def __init__(self) -> None:
        super().__init__()
        BaseMiniboss.inactive_elements.append(self)

    @classmethod
    def spawn(cls, position_anchor : str, position : int|pygame.Vector2):
        raise NotImplementedError("Cannot instanciate base-class BaseEnemy; sub-class must implement this method")

class BasicBoss(BaseBoss):
    active_elements : list['BasicBoss'] = []
    inactive_elements : list['BasicBoss'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseEnemy, BaseBoss]

    basic_boss_image : pygame.Surface = pygame.transform.scale_by(load_alpha_to_colorkey('assets/graphics/enemy/alien.png', 
                                                                                         (0, 255, 0)), 2)
    def __init__(self):
        super().__init__()
        self.control_script : BasicBossEntryScript
        self.health_bar : UiSprite
        self.max_hp : float
        self.invincible : bool
        BasicBoss.inactive_elements.append(self)

    @classmethod
    def spawn(cls):
        element = cls.inactive_elements[0]

        element.image = BasicBoss.basic_boss_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect("midbottom", pygame.Vector2(480, 0))
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.type = 'basic'
        element.max_hp = 50
        element.health = element.max_hp
        element.health_bar = element.create_healthbar_visual()
        element.update_healthbar_visual()
        core_object.main_ui.add(element.health_bar)
        element.health_bar.visible = False
        element.invincible = False

        element.control_script = BasicBossEntryScript()
        element.control_script.initialize(core_object.game.game_timer.get_time, element)

        cls.unpool(element)
        return element
    
    @staticmethod
    def get_healthbar_color(percentage : float):
        colors = {'Dark Green' : 0.8, 'Green' : 0.6, 'Yellow' : 0.4, 'Orange' : 0.2, 'Red' : -1}
        for color, value in colors.items():
            if percentage > value:
                return color

    def create_healthbar_visual(self) -> UiSprite:
        BAR_DIMENSIONS : tuple[int, int] = (50, 5)
        bar_image : pygame.Surface = pygame.Surface(BAR_DIMENSIONS)
        bar_image.fill(self.get_healthbar_color(1.0))
        bar_image.set_colorkey((0, 255, 255))
        new_sprite : UiSprite = UiSprite(bar_image, bar_image.get_rect(midbottom = self.rect.midtop + pygame.Vector2(10, 0)),
                                         -1, 'boss_healthbar')
        return new_sprite
    
    def update_healthbar_visual(self):
        health_percentage : float = self.health / self.max_hp
        self.health_bar.surf.fill((0, 255, 255))
        max_width : int = self.health_bar.rect.width
        bar_height : int = self.health_bar.rect.height
        bar_width : int = int(pygame.math.lerp(0, max_width, health_percentage))
        pygame.draw.rect(self.health_bar.surf, self.get_healthbar_color(health_percentage), (0, 0, bar_width, bar_height))
        self.health_bar.rect.midbottom = self.rect.midtop + pygame.Vector2(0, -5)
    
    def update(self, delta: float):
        next_script = self.control_script.process_frame(delta)
        if next_script:
            self.control_script = next_script
            self.control_script.initialize(core_object.game.game_timer.get_time, self)
        self.check_collisions()
        self.update_healthbar_visual()

    def when_hit(self, projectile : BaseProjectile):
        self.take_damage(projectile.damage)
        overlap_point : tuple[int, int] = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point)
        if self.health <= 0:
            core_object.main_ui.remove(self.health_bar)
            self.kill_instance_safe()
            ParticleEffect.load_effect('boss_killed').play(self.position.copy(), core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx(BaseEnemy.enemy_killed_sfx, 1.0)
        elif not self.invincible:
            ParticleEffect.load_effect('enemy_damaged').play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx(BaseEnemy.enemy_hit_sfx, 1.0)

    def take_damage(self, damage : float):
        if not self.invincible:
            core_object.log(f"Basic boss took damage : {damage:.2f}")
            self.health -= damage
            self.health_bar.visible = True
    
    def fire_homing_projectile(self) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, 5), None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=1,
        homing_targets=Player, team=Teams.ENEMY)
    
    def fire_normal_projectile(self) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, 30), pygame.Vector2(0, 5), None, None, 0,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)
    
    def clean_instance(self):
        super().clean_instance()
        self.control_script = None
        self.invincible = None
        self.max_hp = None
        self.health_bar = None

class BasicBossEntryScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|CoroutineScript:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, CoroutineScript]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        target_position : pygame.Vector2 = pygame.Vector2(centerx, 20) + pygame.Vector2(0, unit.rect.height // 2)
        start_position : pygame.Vector2 = unit.position.copy()
        move_in_timer : Timer = Timer(2, time_source)
        delta = yield
        unit.invincible = True
        if delta is None: delta = core_object.dt
        while not move_in_timer.isover():
            alpha : float = interpolation.smoothstep(move_in_timer.get_time() / move_in_timer.duration)
            new_pos : pygame.Vector2 = start_position.lerp(target_position, alpha)
            unit.position = new_pos
            delta = yield
        unit.position = target_position
        unit.invincible = False
        return BasicBossBehaviorScript()

class BasicBossBehaviorScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|CoroutineScript:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, CoroutineScript]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            delta = yield

def runtime_imports():
    global Player, src
    from src.sprites.player import Player
    import src.sprites.player

Sprite.register_class(BaseBoss)
Sprite.register_class(BaseMiniboss)

Sprite.register_class(BasicBoss)
for _ in range(30): BasicBoss()