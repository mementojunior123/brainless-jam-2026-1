import pygame
from typing import Generator, TypeAlias, Literal, TypedDict
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey, recolor_image
from framework.utils.my_timer import Timer, TimeSource
from framework.core.core import core_object
from framework.game.coroutine_scripts import CoroutineScript
import src.sprites.projectiles
from src.sprites.projectiles import NormalProjectile, BaseProjectile, HomingProjectile, Teams
import src.sprites.enemy
from src.sprites.enemy import BaseEnemy, BaseNormalEnemy
from enum import Enum


class AlternateFireTypes(Enum):
    LAZER = 0
    SHOTGUN = 1

UpgradeType : TypeAlias = Literal['RegularDamageBonus', 'SpecialDamageMultipler', 'AllDamageMultiplier',
                                  'RegularFirerateMultiplier', 'SpecialFirerateMultiplier', 'AllFirerateMultiplier',
                                  'AlternateFireType', 'MaxHealthBonus', 'HealHealth', 'HealMax']

class AlternateFireBaseStatLine(TypedDict):
    damage : float
    firerate : float
    name : str
    description : str

alternate_fire_base_stats : dict[int, AlternateFireBaseStatLine] = {
    AlternateFireTypes.LAZER.value : {
        'damage' : 5,
        'firerate' : 0.25,
        'name' : 'Lazer',
        'description' : 'a lazer type weapon'
    },

    AlternateFireTypes.SHOTGUN.value : {
        'damage' : 2,
        'firerate' : 0.4,
        'name' : 'Shotgun',
        'description' : 'a shotgun type weapon'
    }
}

class Upgrades(TypedDict):
    RegularDamageBonus : float
    SpecialDamageMultipler : float
    AllDamageMultiplier : float

    RegularFirerateMultiplier : float
    SpecialFirerateMultiplier : float
    AllFirerateMultiplier : float

    AlternateFireType : int
    AlternateFireBaseDamage : float # Shotgun damage is per-pellet
    AlternateFireBaseFireRate : float

    MaxHealthBonus : int

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
    BASE_SHOT_FIRERATE : float = 3
    BASE_ALTERNATE_SHOT_FIRERATE : float = 0.25
    BASE_HEALTH : int = 3
    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.animation_images : dict[int, pygame.Surface]
        self.animation_script : PlayerAnimationScript
        self.velocity : pygame.Vector2

        self.max_hp : float
        self.current_hp : float
        self.visible : bool
        self.can_shoot : bool

        self.shot_cooldown_timer : Timer
        self.alternate_fire_cooldown_timer : Timer
        self.upgrades : Upgrades
        self.invuln_timer : Timer
        self.invincible : bool
        Player.inactive_elements.append(self)
    
    @staticmethod
    def get_default_upgrades() -> Upgrades:
        return {
            'RegularDamageBonus' : 0,
            'SpecialDamageMultipler' : 1,
            'AllDamageMultiplier' : 1,

            'RegularFirerateMultiplier' : 1,
            'SpecialFirerateMultiplier' : 1,
            'AllFirerateMultiplier' : 1,

            'AlternateFireType' : AlternateFireTypes.LAZER.value,
            'AlternateFireBaseDamage' : alternate_fire_base_stats[AlternateFireTypes.LAZER.value]['damage'],
            'AlternateFireBaseFireRate' :alternate_fire_base_stats[AlternateFireTypes.LAZER.value]['firerate'],
            
            'MaxHealthBonus' : 0,
        }

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

        element.shot_cooldown_timer = Timer(1 / Player.BASE_SHOT_FIRERATE, core_object.game.game_timer.get_time)
        element.shot_cooldown_timer.start_time -= 1 / Player.BASE_SHOT_FIRERATE
        element.alternate_fire_cooldown_timer = Timer(1 / Player.BASE_ALTERNATE_SHOT_FIRERATE, core_object.game.game_timer.get_time)
        element.alternate_fire_cooldown_timer.start_time -= 1 / Player.BASE_ALTERNATE_SHOT_FIRERATE
        element.visible = True

        element.max_hp = Player.BASE_HEALTH
        element.current_hp = element.max_hp
        element.can_shoot = True
        element.upgrades = Player.get_default_upgrades()
        element.invuln_timer = Timer(0.6, core_object.game.game_timer.get_time)
        element.invuln_timer.start_time -= 0.6
        element.invincible = False

        cls.unpool(element)
        return element

    def draw(self, display : pygame.Surface):
        if not self.visible: return
        return super().draw(display)
    
    def update(self, delta: float):
        self.animation_script.process_frame()
        self.update_movement(delta)
        self.check_input()
        self.check_collision()

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

    def check_input(self):
        if pygame.key.get_pressed()[pygame.K_SPACE]:
            self.shoot(ignore_cooldown=False)
        if pygame.key.get_pressed()[pygame.K_f]:
            if not isinstance(core_object.game.state, core_object.game.STATES.ShopGameState):
                self.perform_alternate_fire(ignore_cooldown=False)
    
    def shoot(self, ignore_cooldown : bool = False) -> BaseProjectile|None:
        if not (self.shot_cooldown_timer.isover() or ignore_cooldown) or not self.can_shoot:
            return None
        
        normal_damage : float = (1 + self.upgrades['RegularDamageBonus']) * self.upgrades['AllDamageMultiplier']
        normal_firerate : float = (Player.BASE_SHOT_FIRERATE * self.upgrades['RegularFirerateMultiplier']) * self.upgrades['AllFirerateMultiplier']
        self.shot_cooldown_timer.set_duration(1 / normal_firerate)
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -10), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image4, "White"), team=Teams.ALLIED,
                                       damage = normal_damage)

    def perform_alternate_fire(self, ignore_cooldown : bool = False) -> BaseProjectile|None:
        if not (self.alternate_fire_cooldown_timer.isover() or ignore_cooldown) or not self.can_shoot:
            return None
        special_damage : float = (self.upgrades['AlternateFireBaseDamage'] * self.upgrades['SpecialDamageMultipler']) * self.upgrades['AllDamageMultiplier']
        special_firerate : float = (self.upgrades['AlternateFireBaseFireRate'] * self.upgrades['SpecialFirerateMultiplier']) * self.upgrades['AllFirerateMultiplier']
        self.alternate_fire_cooldown_timer.set_duration(1 / special_firerate)
        match self.upgrades['AlternateFireType']:
            case AlternateFireTypes.LAZER.value:
                return self.fire_lazer(special_damage)
            case AlternateFireTypes.SHOTGUN.value:
                return (self.fire_shotgun(special_damage))[2]
            case _:
                core_object.log(f"Alternate fire type {self.upgrades['AlternateFireType']} does not exist")
                return None
    
    def fire_lazer(self, damage : int) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -13), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image3, "Purple"), team=Teams.ALLIED,
                                       damage=damage)
    
    def fire_shotgun(self, damage : int) -> list[NormalProjectile]:
        proj_list : list[NormalProjectile] = []
        for angle in (-30, -15, 0, 15, 30):
            proj_list.append(
                NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -13).rotate(angle),
                        None, None, angle, recolor_image(BaseProjectile.normal_image3, "White"), team=Teams.ALLIED,
                        damage=damage)
            )
        return proj_list
    
    def take_damage(self, damage : float):
        if (not self.invuln_timer.isover()) or self.invincible or isinstance(core_object.game.state, core_object.game.STATES.ShopGameState):
            return
        core_object.log(f"Player took damage : {damage}")
        self.current_hp -= damage
        self.invuln_timer.restart()

    def check_collision(self):
        colliding_projectiles : list[BaseProjectile] = [elem for elem in self.get_all_colliding(BaseProjectile) if elem.team in (Teams.ENEMY, Teams.FFA)]
        colliding_enemies : list[BaseEnemy] = self.get_all_colliding(BaseEnemy)
        for enemy in colliding_enemies:
            self.take_damage(1)
            if isinstance(enemy, BaseNormalEnemy):
                enemy.kill_instance()
        for proj in colliding_projectiles:
            self.take_damage(proj.damage)
            proj.kill_instance()

    def clean_instance(self):
        super().clean_instance()
        self.animation_images = None
        self.animation_script = None
        self.velocity = None

        self.max_hp = None
        self.current_hp = None
        self.visible = None

        self.shot_cooldown_timer = None
        self.alternate_fire_cooldown_timer = None
        self.upgrades = None
        self.can_shoot = None

        self.invuln_timer = None
        self.invincible = None

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
            if player.invuln_timer.isover():
                player.visible = True
            else:
                player.visible = (int(player.invuln_timer.get_time() / player.invuln_timer.duration * 3) % 2) != 0
            yield


for _ in range(1): Player()
Sprite.register_class(Player)
