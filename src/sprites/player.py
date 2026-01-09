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
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.particle_effects import ParticleEffect, ParticleEffectTrack

class AlternateFireTypes(Enum):
    LAZER = 0
    SHOTGUN = 1
    ROCKET = 2

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
        'damage' : 4,
        'firerate' : 1.0,
        'name' : 'Lazer',
        'description' : 'A lazer that deals\nhigh damage'
    },

    AlternateFireTypes.SHOTGUN.value : {
        'damage' : 1.5,
        'firerate' : 0.5,
        'name' : 'Shotgun',
        'description' : 'A shotgun that fires\n5 pellets'
    },
    AlternateFireTypes.ROCKET.value : {
        'damage' : 4,
        'firerate' : 0.4,
        'name' : 'Missile',
        'description' : 'A heat-seeking missile\n that deals AOE damage'
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
    heart_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/player/heart2.png", (0, 255, 0))
    empty_heart_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/player/empty_heart4.png", (0, 255, 0))
    hit_sfx : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/player_hit2.ogg")
    hit_sfx.set_volume(0.50)
    normal_shot_sfx : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/normal_shot3.ogg")
    normal_shot_sfx.set_volume(0.5)

    lazer_shot_sfx : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/lazer.ogg")
    lazer_shot_sfx.set_volume(0.4)

    shotgun_shot_sfx : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/shotgun_shot.ogg")
    shotgun_shot_sfx.set_volume(0.7)

    dash_sfx : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/dash.ogg")
    dash_sfx.set_volume(0.4)

    ACCEL_SPEED : float = 3.0
    FRICTION : float = 0.3
    MIN_VELOCITY : float = 0.1
    MAX_VELOCITY : float = 15
    BASE_SHOT_FIRERATE : float = 3
    BASE_ALTERNATE_SHOT_FIRERATE : float = 0.25
    BASE_HEALTH : int = 3

    DASH_COOLDOWN : float = 3
    DASH_DURATION : float = 0.3
    DASH_INVULN_TIME : float = 0.22

    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        self.animation_images : dict[int, pygame.Surface]
        self.animation_script : PlayerAnimationScript
        self.velocity : pygame.Vector2

        self.max_hp : int
        self.current_hp : int
        self.visible : bool
        self.can_shoot : bool

        self.shot_cooldown_timer : Timer
        self.alternate_fire_cooldown_timer : Timer
        self.upgrades : Upgrades
        self.invuln_timer : Timer
        self.invincible : bool

        self.ui_hearts : list[UiSprite]
        self.ui_alternate_fire_sprite : UiSprite
        self.ui_dash_sprite : UiSprite

        self.dash_timer : Timer
        self.dash_direction : int|None
        self.dash_track : ParticleEffectTrack|None

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

            'AlternateFireType' : AlternateFireTypes.ROCKET.value,
            'AlternateFireBaseDamage' : alternate_fire_base_stats[AlternateFireTypes.ROCKET.value]['damage'],
            'AlternateFireBaseFireRate' : alternate_fire_base_stats[AlternateFireTypes.ROCKET.value]['firerate'],
            
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
        element.ui_hearts = []
        element.update_hearts()
        element.ui_alternate_fire_sprite = element.create_alternate_fire_visual()
        element.update_alternate_fire_visual()
        core_object.main_ui.add(element.ui_alternate_fire_sprite)

        element.dash_timer = Timer(Player.DASH_DURATION, core_object.game.game_timer.get_time)
        element.dash_timer.start_time -= Player.DASH_COOLDOWN
        element.dash_direction = None
        element.dash_track = None

        element.ui_dash_sprite = element.create_dash_cooldown_visual()
        element.update_dash_cooldown_visual()
        core_object.main_ui.add(element.ui_dash_sprite)

        

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
        self.update_hearts()
        self.update_alternate_fire_visual()
        self.update_dash_cooldown_visual()
        if self.dash_track:
            if self.dash_track.ended:
                self.dash_track = None
            else:
                self.dash_track.origin = self.position

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
        MARGIN : int = 25
        if self.rect.right > Player.display_size[0] - MARGIN:
            self.rect.right = Player.display_size[0] - MARGIN
            if self.velocity.x > 0: self.velocity.x = 0
        if self.rect.bottom > Player.display_size[1]:
            self.rect.bottom = Player.display_size[1]
        if self.rect.left < MARGIN:
            self.rect.left = MARGIN
            if self.velocity.x < 0: self.velocity.x = 0
        if self.rect.top < 0:
            self.rect.top = 0

    def calculate_acceleration(self) -> pygame.Vector2:
        if not self.dash_timer.isover():
            return pygame.Vector2(self.dash_direction * 7, 0)
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
    
    def attempt_dash(self):
        if self.dash_timer.get_time() <= Player.DASH_COOLDOWN:
            return
        dash_direction : int = 0
        pressed_keys = pygame.key.get_pressed()
        if pressed_keys[pygame.K_a] or pressed_keys[pygame.K_LEFT]:
            dash_direction -= 1
        if pressed_keys[pygame.K_d] or pressed_keys[pygame.K_RIGHT]:
            dash_direction += 1
        if dash_direction == 0:
            return
        self.dash_direction = dash_direction
        self.dash_timer.restart()
        self.velocity += pygame.Vector2(dash_direction * 6, 0)
        self.dash_track = ParticleEffect.load_effect('dash_effect').play(self.position, core_object.game.game_timer.get_time)
        self.dash_track.origin = self.position
        core_object.bg_manager.play_sfx(self.dash_sfx, volume=1.0)
    
    def get_normal_damage(self) -> float:
        return (1 + self.upgrades['RegularDamageBonus']) * self.upgrades['AllDamageMultiplier']
    
    def get_normal_firerate(self) -> float:
        return (Player.BASE_SHOT_FIRERATE * self.upgrades['RegularFirerateMultiplier']) * self.upgrades['AllFirerateMultiplier']
    
    def get_special_damage(self) -> float:
        return (self.upgrades['AlternateFireBaseDamage'] * self.upgrades['SpecialDamageMultipler']) * self.upgrades['AllDamageMultiplier']

    def get_special_firerate(self) -> float:
        return (self.upgrades['AlternateFireBaseFireRate'] * self.upgrades['SpecialFirerateMultiplier']) * self.upgrades['AllFirerateMultiplier']

    
    def shoot(self, ignore_cooldown : bool = False) -> BaseProjectile|None:
        if not (self.shot_cooldown_timer.isover() or ignore_cooldown) or not self.can_shoot:
            return None
        
        normal_damage : float = self.get_normal_damage()
        normal_firerate : float = self.get_normal_firerate()
        self.shot_cooldown_timer.set_duration(1 / normal_firerate)
        core_object.bg_manager.play_sfx(Player.normal_shot_sfx, 1.0)
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -10), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image3, "White"), team=Teams.ALLIED,
                                       damage = normal_damage, can_destroy=True)

    def perform_alternate_fire(self, ignore_cooldown : bool = False) -> BaseProjectile|None:
        if not (self.alternate_fire_cooldown_timer.isover() or ignore_cooldown) or not self.can_shoot:
            return None
        special_damage : float = self.get_special_damage()
        special_firerate : float = self.get_special_firerate()
        self.alternate_fire_cooldown_timer.set_duration(1 / special_firerate)
        match self.upgrades['AlternateFireType']:
            case AlternateFireTypes.LAZER.value:
                return self.fire_lazer(special_damage)
            case AlternateFireTypes.SHOTGUN.value:
                return (self.fire_shotgun(special_damage))[2]
            case AlternateFireTypes.ROCKET.value:
                return self.fire_rocket(special_damage)
            case _:
                core_object.log(f"Alternate fire type {self.upgrades['AlternateFireType']} does not exist")
                return None
    
    def fire_lazer(self, damage : int) -> NormalProjectile:
        core_object.bg_manager.play_sfx(Player.lazer_shot_sfx, 1.0)
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -16), None, None, 0,
                                       recolor_image(BaseProjectile.normal_image3, "Purple"), team=Teams.ALLIED,
                                       damage=damage, can_destroy=True)
    
    def fire_shotgun(self, damage : int) -> list[NormalProjectile]:
        core_object.bg_manager.play_sfx(Player.shotgun_shot_sfx, 1.0)
        proj_list : list[NormalProjectile] = []
        for angle in (-20, -10, 0, 10, 20):
            proj_list.append(
                NormalProjectile.spawn(self.position + pygame.Vector2(0, -30), pygame.Vector2(0, -16).rotate(angle),
                        None, None, angle, recolor_image(BaseProjectile.normal_image4, "White"), team=Teams.ALLIED,
                        damage=damage, can_destroy=True)
            )
        return proj_list
    
    def fire_rocket(self, damage : float) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, -30), 
                                      pygame.Vector2(0, -10), 
                                      None, None, 0,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=3,
        homing_targets=BaseEnemy, team=Teams.ALLIED, can_destroy=True, damage=damage, die_after_destroying=False,
        explosion_damage=damage/2, explosive_range=250)
    
    def take_damage(self, damage : float):
        if ((not self.invuln_timer.isover()) 
            or self.invincible 
            or isinstance(core_object.game.state, core_object.game.STATES.ShopGameState)
            or (self.dash_timer.get_time() < Player.DASH_INVULN_TIME)):
            return
        core_object.log(f"Player took damage : {damage}")
        self.current_hp -= damage
        self.invuln_timer.restart()
        core_object.bg_manager.play_sfx(Player.hit_sfx, 1.0)

    def check_collision(self):
        colliding_projectiles : list[BaseProjectile] = [elem for elem in self.get_all_colliding(BaseProjectile) if elem.team in (Teams.ENEMY, Teams.FFA)]
        colliding_enemies : list[BaseEnemy] = self.get_all_colliding(BaseEnemy)
        for enemy in colliding_enemies:
            self.take_damage(1)
            if isinstance(enemy, BaseNormalEnemy):
                enemy.kill_instance()
        if self.dash_timer.get_time() < Player.DASH_INVULN_TIME:
            return
        for proj in colliding_projectiles:
            self.take_damage(proj.damage)
            proj.kill_instance()
    
    def update_hearts(self):
        ui_heart_count : int = len(self.ui_hearts)
        ui_desync_diff : int = ui_heart_count - self.max_hp
        if ui_desync_diff == 0:
            pass
        elif ui_desync_diff > 0:
            for _ in range(ui_desync_diff):
                to_remove = self.ui_hearts.pop(-1)
                core_object.main_ui.remove(to_remove)
        else:
            for _ in range(abs(ui_desync_diff)):
                GAP : int = 5
                top : int = 10
                prev_left : int = self.ui_hearts[-1].rect.left if self.ui_hearts else Player.display_size[0] - 1
                new_sprite = UiSprite(self.heart_image, self.heart_image.get_rect(topright=(prev_left - GAP, top)),
                                               -1, 'ui_heart', colorkey=(0, 255, 0))
                self.ui_hearts.append(new_sprite)
                core_object.main_ui.add(new_sprite)
        
        colored_heart_count : int = self.current_hp
        for heart in self.ui_hearts:
            heart.surf = Player.heart_image if colored_heart_count > 0 else Player.empty_heart_image
            colored_heart_count -= 1
    
    def create_alternate_fire_visual(self) -> UiSprite:
        BAR_DIMENSIONS : tuple[int, int] = (2, 50)
        bar_image : pygame.Surface = pygame.Surface(BAR_DIMENSIONS)
        bar_image.fill((0, 255, 0))
        bar_image.set_colorkey((0, 255, 0))
        new_sprite : UiSprite = UiSprite(bar_image, bar_image.get_rect(midleft = self.rect.midright + pygame.Vector2(10, 0)),
                                         -1, 'alternate_fire_cooldown')
        return new_sprite
    
    def update_alternate_fire_visual(self):
        self.ui_alternate_fire_sprite.surf.fill((0, 255, 0))
        bar_width : int = self.ui_alternate_fire_sprite.rect.width
        max_height : int = self.ui_alternate_fire_sprite.rect.height
        ready_percentage : float = self.alternate_fire_cooldown_timer.get_time() / self.alternate_fire_cooldown_timer.duration
        bar_height : int = int(pygame.math.lerp(max_height, 0, ready_percentage))
        pygame.draw.rect(self.ui_alternate_fire_sprite.surf, 'White', (0, max_height - bar_height, bar_width, bar_height))
        self.ui_alternate_fire_sprite.rect.midleft = self.rect.midright + pygame.Vector2(10, 0)
    
    def create_dash_cooldown_visual(self) -> UiSprite:
        BAR_DIMENSIONS : tuple[int, int] = (50, 2)
        bar_image : pygame.Surface = pygame.Surface(BAR_DIMENSIONS)
        bar_image.fill((0, 255, 0))
        bar_image.set_colorkey((0, 255, 0))
        new_sprite : UiSprite = UiSprite(bar_image, bar_image.get_rect(midtop = self.rect.midbottom + pygame.Vector2(0, 10)),
                                         -1, 'dash_cooldown')
        return new_sprite
    
    def update_dash_cooldown_visual(self):
        self.ui_dash_sprite.surf.fill((0, 255, 0))
        max_width : int = self.ui_dash_sprite.rect.width
        bar_height : int = self.ui_dash_sprite.rect.height
        ready_percentage : float = self.dash_timer.get_time() / Player.DASH_COOLDOWN
        bar_width : int = int(pygame.math.lerp(max_width, 0, ready_percentage))
        pygame.draw.rect(self.ui_dash_sprite.surf, 'White', (0, 0, bar_width, bar_height))
        self.ui_dash_sprite.rect.midtop = self.rect.midbottom + pygame.Vector2(0, 4)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LSHIFT:
                self.attempt_dash()

    @classmethod
    def receive_key_event(cls, event : pygame.Event):
        for elem in cls.active_elements:
            elem.handle_key_event(event)
        

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
        self.ui_hearts = None
        self.ui_alternate_fire_sprite = None
        self.ui_dash_sprite = None

        self.dash_timer = None
        self.dash_direction = None
        self.dash_track = None

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


def make_connections():
    core_object.event_manager.bind(pygame.KEYDOWN, Player.receive_key_event)
    core_object.event_manager.bind(pygame.KEYUP, Player.receive_key_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.KEYDOWN, Player.receive_key_event)
    core_object.event_manager.unbind(pygame.KEYUP, Player.receive_key_event)

for _ in range(1): Player()
Sprite.register_class(Player)
