import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import sign, load_alpha_to_colorkey, ColorType
from enum import Enum
from inspect import isclass

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

    normal_image1 : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_1-white.png", (0, 255, 0))
    normal_image2 : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_2-white.png", (0, 255, 0))
    normal_image3 : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_3-white.png", (0, 255, 0))
    normal_image4 : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/normal_projectile_4-white.png", (0, 255, 0))


    def __init__(self) -> None:
        super().__init__()
        self.velocity : pygame.Vector2
        self.acceleration : pygame.Vector2
        self.drag : float

        self.type : str
        self.was_onscreen_once : bool
        self.team : Teams
        self.damage : float
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
    
    def clean_instance(self):
        super().clean_instance()
        self.velocity = None
        self.acceleration = None
        self.drag = None

        self.type = None
        self.was_onscreen_once = None
        self.team = None
        self.damage = None

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
              zindex : int = 0, damage : float = 1):
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

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
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
        HomingProjectile.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2, velocity : pygame.Vector2|None, accel : pygame.Vector2|None, drag : float|None, 
              angle_offset : float, custom_image : pygame.Surface, team : Teams = Teams.PACIFIST, 
              projectile_type : str = "", pivot_offset : pygame.Vector2|None = None,
              zindex : int = 0, homing_range : float = 1000, homing_rate : float = 3, 
              homing_targets : list[list[Sprite]|Sprite]|None = None, damage : float = 1):
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

        element.homing_targets = homing_targets
        element.homing_range = homing_range
        element.homing_rate = homing_rate

        element.angle = angle_offset + (element.get_velocity_orientation() or 0)

        cls.unpool(element)
        return element
    
    def update(self, delta : float):
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

Sprite.register_class(BaseProjectile)
Sprite.register_class(NormalProjectile)
Sprite.register_class(HomingProjectile)
for _ in range(200):
    NormalProjectile()

for _ in range(50):
    HomingProjectile()


def make_connections():
    pass

def remove_connections():
    pass