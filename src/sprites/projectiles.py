import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import sign, load_alpha_to_colorkey, ColorType, remove_image_empty
from enum import Enum
from inspect import isclass
from typing import Union
from framework.utils.particle_effects import ParticleEffect

class Teams(Enum):
    PACIFIST = "Pacifist"
    FFA = "FFA"
    ALLIED = "Allied"
    ENEMY = "Enemy"

class BaseProjectile(Sprite):
    test_image_size : int = 10
    test_image = pygame.Surface((test_image_size, test_image_size))
    test_image.fill((0, 255, 0))
    active_elements : list['BaseProjectile'] = []
    inactive_elements : list['BaseProjectile'] = []
    linked_classes : list['Sprite'] = [Sprite]

    rocket_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/rocket.png", (0, 255, 0))

    normal_image1 : pygame.Surface = remove_image_empty(load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_1-white.png", (0, 255, 0)))
    normal_image2 : pygame.Surface = remove_image_empty(load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_2-white.png", (0, 255, 0)))
    normal_image3 : pygame.Surface = remove_image_empty(load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_3-white.png", (0, 255, 0)))
    normal_image4 : pygame.Surface = remove_image_empty(load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_4-white.png", (0, 255, 0))
)
    explosion_sfx1 : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/sfx/explosion1.ogg")
    explosion_sfx1.set_volume(0.7)
    bounding_box : pygame.Rect = pygame.Rect(0, 0, *core_object.main_display.get_size())

    def __init__(self) -> None:
        super().__init__()
        self.velocity : pygame.Vector2
        self.acceleration : pygame.Vector2
        self.drag : float

        self.type : str
        self.was_onscreen_once : bool
        self.team : Teams
        self.damage : float

        self.can_destroy : bool
        self.destructible : bool
        self.die_after_destroying : bool
        BaseProjectile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, velocity : pygame.Vector2, accel : pygame.Vector2, drag : float, angle : float):
        
        raise NotImplementedError("Cannot instanciate base-class BaseProjectile; sub-class must implement this method")
        element = cls.inactive_elements[0]
        element.image = cls.test_image
        element.rect = element.image.get_rect()
        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.velocity = velocity if velocity and velocity.magnitude() > 0 else pygame.Vector2(0, 0)
        element.acceleration = accel if accel and accel.magnitude() > 0 else pygame.Vector2(0, 0)
        element.drag = drag if drag is not None else 0
        element.pivot = Pivot2D(element._position, element.image, (0, 255, 255))
        element.pivot.pivot_offset = pygame.Vector2(0, 0)
        element.angle = angle

        element.mask = pygame.mask.from_surface(element.image)
        
        cls.unpool(element)
        
        return element
    
    def update(self, delta : float):
        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5

        self.velocity += self.acceleration * 0.5 * delta
        self.position += self.velocity * delta
        self.velocity += self.acceleration * 0.5 * delta

        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
    
    def check_destruction(self):
        if not self.destructible:
            return
        projectile : BaseProjectile
        for projectile in self.get_all_colliding(BaseProjectile):
            if projectile == self:
                continue
            if projectile.team == Teams.PACIFIST:
                continue
            if projectile.team == self.team and (self.team != Teams.FFA):
                continue
            if projectile.can_destroy:
                overlap_point : tuple[int, int] = self.mask.overlap(self.mask, (self.rect.x - projectile.rect.x, self.rect.y - projectile.rect.y)) or (self.rect.width // 2, self.rect.height // 2)
                point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point)
                ParticleEffect.load_effect('explosion_small_effect').play(point_of_contact, core_object.game.game_timer.get_time)
                core_object.bg_manager.play_sfx(BaseProjectile.explosion_sfx1, 0.75)
                self.kill_instance_safe()
            if projectile.die_after_destroying:
                projectile.kill_instance_safe()
    
    def clean_instance(self):
        super().clean_instance()
        self.velocity = None
        self.acceleration = None
        self.drag = None

        self.type = None
        self.was_onscreen_once = None
        self.team = None
        self.damage = None

        self.destructible = None
        self.die_after_destroying = None
        self.can_destroy = None

class NormalProjectile(BaseProjectile):
    active_elements : list['NormalProjectile'] = []
    inactive_elements : list['NormalProjectile'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseProjectile]

    def __init__(self) -> None:
        super().__init__()
        NormalProjectile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, velocity : pygame.Vector2|None, accel : pygame.Vector2|None, drag : float|None, angle : float,
              custom_image : pygame.Surface, team : Teams = Teams.PACIFIST, 
              projectile_type : str = "", pivot_offset : pygame.Vector2|None = None,
              zindex : int = 0, damage : float = 1, can_destroy : bool = False, destructible : bool = False, 
              die_after_destroying : bool = True):
        element = cls.inactive_elements[0]

        element.image = custom_image
        element.rect = element.image.get_rect()
        element.position = new_pos
        element.align_rect()
        element.zindex = zindex

        element.velocity = velocity if velocity and velocity.magnitude() > 0 else pygame.Vector2(0, 0)
        element.acceleration = accel if accel and accel.magnitude() > 0 else pygame.Vector2(0, 0)
        element.drag = drag if drag is not None else 0
        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 255))
        element.pivot.pivot_offset = pygame.Vector2(0, 0) if pivot_offset is None else pivot_offset
        element.angle = angle
        element.team = team

        element.type = projectile_type
        element.mask = pygame.mask.from_surface(element.image)
        element.was_onscreen_once = False
        element.damage = damage

        element.can_destroy = can_destroy
        element.destructible = destructible
        element.die_after_destroying = die_after_destroying

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
        if self._zombie:
            return
        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5

        self.velocity += self.acceleration * 0.5 * delta
        self.position += self.velocity * delta
        self.velocity += self.acceleration * 0.5 * delta

        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
        if not self.rect.colliderect((0, 0, *core_object.main_display.get_size())):
            if self.was_onscreen_once:
                self.kill_instance_safe()
        else:
            self.was_onscreen_once = True
        if not self._zombie:
            self.check_destruction()
    
    def clean_instance(self):
        super().clean_instance()
        

class HomingProjectile(BaseProjectile):
    default_image_size : tuple[int, int] = (20, 10)
    default_image = pygame.Surface(default_image_size)
    default_image.fill((0, 255, 0))
    active_elements : list['HomingProjectile'] = []
    inactive_elements : list['HomingProjectile'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseProjectile]

    def __init__(self) -> None:
        super().__init__()
        self.homing_range : float
        self.homing_rate : float
        self.homing_targets : list[list[Sprite]|Sprite]
        self.dynamic_mask = True
        self.angle_offset : float
        self.explosive_range : float
        self.explosive_damage : float
        HomingProjectile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, velocity : pygame.Vector2|None, accel : pygame.Vector2|None, drag : float|None, 
              angle_offset : float, custom_image : pygame.Surface, team : Teams = Teams.PACIFIST, 
              projectile_type : str = "", pivot_offset : pygame.Vector2|None = None,
              zindex : int = 0, homing_range : float = 1000, homing_rate : float = 3, 
              homing_targets : list[list[Sprite]|Sprite]|None = None, damage : float = 1, 
              can_destroy : bool = False, destructible : bool = False, die_after_destroying : bool = True,
              explosive_range : float = 0, explosion_damage : float = 0):
        if homing_targets is None: homing_targets = []
        if not isinstance(homing_targets, list):
            homing_targets = [homing_targets]
        element = cls.inactive_elements[0]

        element.image = custom_image
        element.rect = element.image.get_rect()
        element.position = new_pos
        element.align_rect()
        element.zindex = zindex

        element.velocity = velocity if velocity and velocity.magnitude() > 0 else pygame.Vector2(0, 0)
        element.acceleration = accel if accel and accel.magnitude() > 0 else pygame.Vector2(0, 0)
        element.drag = drag if drag is not None else 0
        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 255))
        element.pivot.pivot_offset = pygame.Vector2(0, 0) if pivot_offset is None else pivot_offset
        element.angle_offset = angle_offset
        element.mask = pygame.mask.from_surface(element.image)

        element.team = team
        element.type = projectile_type
        element.was_onscreen_once = False
        element.damage = damage

        element.can_destroy = can_destroy
        element.destructible = destructible
        element.die_after_destroying = die_after_destroying

        element.homing_targets = homing_targets
        element.homing_range = homing_range
        element.homing_rate = homing_rate

        element.angle = angle_offset + (element.get_velocity_orientation() or 0)

        element.explosive_range = explosive_range
        element.explosive_damage = explosion_damage

        cls.unpool(element)
        return element
    
    def explode(self, hit : Union["BaseEnemy", "Player"]):
        overlap_point : tuple[int, int] = self.mask.overlap(self.mask, (self.rect.x - hit.rect.x, self.rect.y - hit.rect.y)) or (self.rect.width // 2, self.rect.height // 2)
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point)
        got_a_kill : bool = False if getattr(hit, 'current_hp', getattr(hit, 'health')) > 0 else True
        if self.team == Teams.ALLIED or self.team == Teams.FFA:
            for enemy in BaseEnemy.active_elements:
                if enemy == hit:
                    continue
                if (self.position - enemy.position).magnitude() < self.explosive_range:
                    enemy.take_damage(self.explosive_damage)
                    enemy.give_score(1)
                    if enemy.health < 0:
                        if isinstance(enemy, BaseNormalEnemy):
                            enemy.kill_instance_safe()
                            got_a_kill = True
                            enemy.give_score(enemy.KILL_SCORE)
                            ParticleEffect.load_effect('enemy_killed').play(enemy.position, core_object.game.game_timer.get_time)
                            core_object.bg_manager.play_sfx(BaseEnemy.enemy_killed_sfx, 1.0)
                    else:
                        ParticleEffect.load_effect('enemy_damaged').play(enemy.position, core_object.game.game_timer.get_time)
                        core_object.bg_manager.play_sfx(BaseEnemy.enemy_hit_sfx, 1.0)
        if self.team == Teams.ENEMY or self.team == Teams.FFA:
            for player in Player.active_elements:
                if player == hit:
                    continue
                if (self.position - player.position).magnitude() < self.explosive_range:
                    player.take_damage(self.explosive_damage)
        effect_played = 'explosion_effect' if got_a_kill else 'explosion_small_effect'
        ParticleEffect.load_effect(effect_played).play(point_of_contact, core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx(BaseProjectile.explosion_sfx1, 1.0)

    def update(self, delta : float):
        if self._zombie:
            return
        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
        self.update_orientation_half(delta)
        self.velocity += self.acceleration * 0.5 * delta
        self.position += self.velocity * delta
        self.update_orientation_half(delta)
        self.velocity += self.acceleration * 0.5 * delta

        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
        if not self.rect.colliderect((0, 0, *core_object.main_display.get_size())):
            if self.was_onscreen_once:
                self.kill_instance_safe()
        else:
            self.was_onscreen_once = True
        if not self._zombie:
            self.check_destruction()
    
    def pick_homing_target(self) -> Sprite|None:
        if not self.homing_targets: return None
        groups : list[list[Sprite]|Sprite] = [grp.active_elements if isclass(grp) else grp for grp in self.homing_targets]
        targets : list[Sprite] = []
        for grp in groups:
            if isinstance(grp, list):
                targets.extend(grp)
            else:
                targets.append(grp)
        if not targets:
            return None
        targets.sort(key=lambda sprite : (self.position - sprite.position).magnitude())
        if (self.position - targets[0].position).magnitude() > self.homing_range:
            return None
        return targets[0]
    
    def update_orientation_half(self, delta : float):
        target : Sprite|None = self.pick_homing_target()
        if target is None:
            return
        vec_to_target : pygame.Vector2 = target.position - self.position
        to_rotate : float = self.velocity.angle_to(vec_to_target)
        if (self.homing_rate * delta * 0.5) >= abs(to_rotate):
            self.velocity.rotate_ip(to_rotate)
        else:
            self.velocity.rotate_ip(self.homing_rate * delta * 0.5 * sign(to_rotate))
        self.angle = self.angle_offset + (self.get_velocity_orientation() or 0)

    def change_velocity_orientation(self):
        pass
    
    def get_velocity_orientation(self) -> float|None:
        if self.velocity.magnitude() <= 0:
            return None
        else:
            return pygame.Vector2(0, -1).angle_to(self.velocity)
    
    def clean_instance(self):
        super().clean_instance()
        self.homing_range = None
        self.homing_rate = None
        self.homing_targets = None
        self.dynamic_mask = None
        self.angle_offset = None
        self.explosive_range = None
        self.explosive_damage = None

class ScatterProjectile(BaseProjectile):
    active_elements : list['ScatterProjectile'] = []
    inactive_elements : list['ScatterProjectile'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseProjectile]

    def __init__(self) -> None:
        super().__init__()
        self.og_bounce_count : int
        self.scatter_count : int
        self.scatter_proj_num : int
        self.ignore : list[Sprite]
        self.bounces_left : int
        self.scatter_reflect : bool
        self.damage_decay : float
        self.angle_offset : float
        ScatterProjectile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, velocity : pygame.Vector2|None, accel : pygame.Vector2|None, drag : float|None, angle : float,
              custom_image : pygame.Surface, team : Teams = Teams.PACIFIST, 
              projectile_type : str = "", pivot_offset : pygame.Vector2|None = None,
              zindex : int = 0, damage : float = 1, can_destroy : bool = False, destructible : bool = False, 
              die_after_destroying : bool = True, 
              bounce_count : int = 2, scatter_count : int = 1, scatter_proj_num : int = 3,
              ignore : list["Sprite"]|None = None, scatter_reflect : bool = False, damage_decay : float = 1.0,
              angle_offset : float = 0.0):
        element = cls.inactive_elements[0]

        element.image = custom_image
        element.rect = element.image.get_rect()
        element.position = new_pos
        element.align_rect()
        element.zindex = zindex

        element.velocity = velocity if velocity and velocity.magnitude() > 0 else pygame.Vector2(0, 0)
        element.acceleration = accel if accel and accel.magnitude() > 0 else pygame.Vector2(0, 0)
        element.drag = drag if drag is not None else 0
        element.pivot = Pivot2D(element._position, element.image, element.image.get_colorkey() or (0, 255, 255))
        element.pivot.pivot_offset = pygame.Vector2(0, 0) if pivot_offset is None else pivot_offset
        element.angle = angle + angle_offset
        element.team = team

        element.type = projectile_type
        element.mask = pygame.mask.from_surface(element.image)
        element.was_onscreen_once = False
        element.damage = damage

        element.can_destroy = can_destroy
        element.destructible = destructible
        element.die_after_destroying = die_after_destroying

        element.og_bounce_count = bounce_count
        element.bounces_left = bounce_count
        element.scatter_count = scatter_count
        element.scatter_proj_num = scatter_proj_num
        element.ignore = ignore or []
        element.scatter_reflect = scatter_reflect
        element.damage_decay = damage_decay
        element.angle_offset = angle_offset

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
        if self._zombie:
            return
        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5

        self.velocity += self.acceleration * 0.5 * delta
        self.position += self.velocity * delta
        self.velocity += self.acceleration * 0.5 * delta

        self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
        walls : list[tuple[pygame.Vector2, pygame.Vector2]] = [
            (pygame.Vector2(0, 0), pygame.Vector2(0, BaseProjectile.bounding_box.height)),
            (pygame.Vector2(0, BaseProjectile.bounding_box.height), pygame.Vector2(*BaseProjectile.bounding_box.size)),
            (pygame.Vector2(*BaseProjectile.bounding_box.size), pygame.Vector2(BaseProjectile.bounding_box.width, 0)),
            (pygame.Vector2(BaseProjectile.bounding_box.width, 0), pygame.Vector2(0, 0)),
        ]
        for wall in walls:
            if (self.bounces_left <= 0) and (self.og_bounce_count >= 0):
                break
            if self.rect.clipline(*wall):
                self.bounce(wall)
        if not self.rect.colliderect((0, 0, *core_object.main_display.get_size())):
            if self.was_onscreen_once:
                self.kill_instance_safe()
        else:
            self.was_onscreen_once = True
        if not self._zombie:
            self.check_destruction()
    
    def scatter(self, hit : "BaseEnemy"):
        self.ignore.append(hit)
        if self.scatter_count <= 0:
            return
        overlap_point : tuple[int, int] = self.mask.overlap(self.mask, (self.rect.x - hit.rect.x, self.rect.y - hit.rect.y)) or (self.rect.width // 2, self.rect.height // 2)
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point) if not self.scatter_reflect else hit.position
        ParticleEffect.load_effect('enemy_damaged').play(point_of_contact, core_object.game.game_timer.get_time)
        velocity_angle : float = self.get_velocity_orientation()
        if velocity_angle is None: return
        velocity_magnitude : float = self.velocity.magnitude()
        for offset in self.generate_angle_offset_list(self.scatter_proj_num, not self.scatter_reflect):
            new_velocity : pygame.Vector2 = self.velocity.rotate(offset)
            new_velocity.scale_to_length(1)
            new_position : pygame.Vector2 = point_of_contact + new_velocity * (0)
            new_velocity.scale_to_length(velocity_magnitude)
            ScatterProjectile.spawn(new_position, new_velocity, self.acceleration, self.drag, pygame.Vector2(0, -1).angle_to(new_velocity),
                                    self.image, self.team, self.type, self.pivot.pivot_offset, self.zindex, self.damage * self.damage_decay,
                                    self.can_destroy, self.destructible, self.die_after_destroying, self.og_bounce_count,
                                    self.scatter_count - 1, self.scatter_proj_num, self.ignore, self.scatter_reflect, self.damage_decay, -self.angle)
    
    @staticmethod
    def generate_angle_offset_list(count : int, add_offset : bool = True) -> list[float]:
        gap : float = 360 / count
        init_offset : float = gap / 2 if add_offset else 0
        return [init_offset + (i * gap) for i in range(count)]
    
    def get_velocity_orientation(self) -> float|None:
        if self.velocity.magnitude() <= 0:
            return None
        else:
            return pygame.Vector2(0, -1).angle_to(self.velocity)
    
    def bounce(self, wall : tuple[pygame.Vector2, pygame.Vector2]):
        self.bounces_left -= 1
        normal : pygame.Vector2 = (wall[1] - wall[0]).rotate(-90)
        normal.scale_to_length(1)
        self.velocity.reflect_ip(normal)
        self.angle = (self.get_velocity_orientation() or self.angle) + self.angle_offset
        while self.rect.clipline(wall):
            self.position += normal
            self.align_rect()
    
    def clean_instance(self):
        super().clean_instance()
        self.scatter_proj_num = None
        self.og_bounce_count = None
        self.scatter_count = None
        self.ignore = None
        self.bounces_left = None
        self.scatter_reflect = None
        self.damage_decay = None
        self.angle_offset = None

Sprite.register_class(BaseProjectile)
Sprite.register_class(NormalProjectile)
Sprite.register_class(HomingProjectile)
Sprite.register_class(ScatterProjectile)
for _ in range(200):
    NormalProjectile()

for _ in range(50):
    HomingProjectile()

for _ in range(50):
    ScatterProjectile()

def runtime_imports():
    global src
    global BaseEnemy, BaseNormalEnemy
    import src.sprites.enemy
    from src.sprites.enemy import BaseEnemy, BaseNormalEnemy

    global Player
    import src.sprites.player
    from src.sprites.player import Player


def make_connections():
    pass

def remove_connections():
    pass