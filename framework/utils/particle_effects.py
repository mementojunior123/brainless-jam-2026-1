import pygame
from framework.utils.my_timer import Timer, TimeSource
from framework.utils.animation import Animation
import framework.utils.interpolation as interpolation
from random import random
from math import sin, radians, cos, atan2
from framework.game.sprite import Sprite
from framework.utils.pivot_2d import Pivot2D
from framework.utils.helpers import load_alpha_to_colorkey
from typing import TypedDict, Literal, Union, TypeAlias

def __random_float(a, b):
    return random() * (b-a) + a

def rand_float(iterable):
    if iterable is None: return iterable
    t = type(iterable)
    if t == int or t == float: return iterable
    return __random_float(iterable[0], iterable[1])


def vec_from_angle(angle : float, magnitude = 1) -> pygame.Vector2:
    x = cos(radians(angle))
    y = -sin(radians(angle))
    return pygame.Vector2(x, y) * magnitude

def get_vec_angle(vec : pygame.Vector2) -> float:
    return atan2(-vec.y, vec.x)

NumberRange : TypeAlias = Union[float, tuple[float, float], list[float]]
UpdateMethod : TypeAlias = Literal['simulated', 'animated', 'spiral']

class EffectData(TypedDict):
    offset_x : NumberRange
    offset_y : NumberRange
    velocity_x : NumberRange|None
    velocity_y : NumberRange|None
    angle : NumberRange|None
    speed : NumberRange|None    
    accel_x : NumberRange|None
    accel_y : NumberRange|None
    drag : NumberRange|None
    init_spawn_count : int
    cooldown : float
    target_spawn_count : int 
    lifetime : NumberRange 
    part_per_wave : int
    main_texture : pygame.Surface
    alt_textures : None|list[pygame.Surface]
    animation : None|Animation
    update_method : UpdateMethod
    destroy_offscreen : bool
    copy_surface : bool
    type : None|str

class Particle(Sprite):
    active_elements : list['Particle'] = []
    inactive_elements : list['Particle']  = []
    linked_classes : list[Sprite] = [Sprite]

    test_image = pygame.surface.Surface((4,4))
    pygame.draw.rect(test_image, 'White', (0, 0, 4, 4))
    spark_particle_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/projectiles/fire_particle.png", (0, 255, 0))
    bounding_box = pygame.Rect(0, 0, 960, 540)

    def __init__(self) -> None:
        super().__init__()
        self.lifetime : float
        self.lifetime_timer : Timer

        self.velocity : pygame.Vector2
        self.acceleration : pygame.Vector2
        self.drag : float

        self.update_method : UpdateMethod = 'simulated'
        self.textures : list[pygame.Surface]
        self.kill_offscreen = True
        Particle.inactive_elements.append(self)
    
    def spawn(self, pos, lifetime, update_method, main_texture : pygame.Surface, velocity = None, accel = None, drag = None, 
              alt_textures = None, anim : Animation = None, destroy_offscreen : bool = False, angle = None, mag = None, copy_surf = False,
              time_source : TimeSource|None = None):
        self.zindex = 100
        self._position = pos
        self.update_method = update_method
        if copy_surf is False:
            self.image = main_texture
            self.textures = alt_textures or []
        else:
            self.image = main_texture.copy()
            if alt_textures is None: self.textures = []
            else: self.textures = [surf.copy() for surf in alt_textures]

        self.rect = self.image.get_rect()
        self.rect.center = self.position

        self.lifetime = lifetime
        self.lifetime_timer = Timer(lifetime, time_source=time_source)

        
        self.velocity = velocity or pygame.Vector2(0,0)
        if self.update_method == 'spiral':
            self.pivot = Pivot2D(self._position, self.image)
            self.pivot.pivot_offset = pygame.Vector2((mag or 1),0).rotate(-angle)
        elif angle is not None:
            if mag is None: mag = 1
            self.velocity += vec_from_angle(angle, mag)
        self.acceleration = accel or pygame.Vector2(0,0)
        self.drag = drag or 0
        self.kill_offscreen= destroy_offscreen

        if anim:
            self.anim_track = anim.load(self)
            self.anim_track.play()
        else:
            self.anim_track = None
        
        Particle.unpool(self)
        self.rect.center = self.pivot.position if self.pivot else self._position
        self.current_camera = core_object.game.main_camera
    
    def update(self, delta : float):
        if self.lifetime_timer.isover():
            self.kill_instance_safe()
            return
        if self.kill_offscreen:
            if self.rect.colliderect(Particle.bounding_box) is False:
                self.kill_instance_safe()
                return
        if self.update_method == 'simulated':
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5

            self.velocity += self.acceleration * 0.5 * delta
            self.position += self.velocity * delta
            self.velocity += self.acceleration * 0.5 * delta

            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.rect.center = self.position
            if self.anim_track is not None:
                self.anim_track.update()
        elif self.update_method == 'spiral':
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.velocity += self.acceleration * 0.5 * delta
            current_distance_to_center : float = self.pivot.pivot_offset.magnitude()
            if current_distance_to_center:
                self.pivot.pivot_offset.rotate_ip(-self.velocity.x * delta)
                self.pivot.pivot_offset.scale_to_length(current_distance_to_center + self.velocity.y * delta)
            self.velocity += self.acceleration * 0.5 * delta
            self.velocity *=  ((1 - self.drag) ** delta) ** 0.5
            self.rect.center = self.pivot.position
            if self.anim_track is not None:
                self.anim_track.update()
        
        elif self.update_method == 'animated':
            self.anim_track.update()

    def clean_instance(self):
        self._position = None
        self.lifetime = None
        self.lifetime_timer = None
        self.pivot = None

        self.velocity = None
        self.acceleration = None
        self.drag = None

        self.update_method = None
        self.image = None
        self.rect = None
        self.textures = None
        self.kill_offscreen = None

for _ in range(250):
    Particle()

class ParticleEffect:
    elements : list['ParticleEffect'] = []
    effects_data : dict[str, EffectData] = {}
    special_effect_name_dict : dict[str, 'ParticleEffect'] = {}
    def __init__(self, data : EffectData, persistance : bool, dynamic_origin : bool = False) -> None:
        self.data : EffectData = data
        ParticleEffect.elements.append(self)
        self.tracks : list[ParticleEffectTrack] = []
        self.plays_remaining = None
        self.started_playing_once : bool = False
        self.destroy_on_end : bool = True
        self.is_persistent : bool = persistance
        self.dynamic_origin : bool = dynamic_origin
        self.position : pygame.Vector2 = pygame.Vector2(0,0)
        self._zombie : bool = False
    
    @classmethod
    def load_effect(cls, name : str, persistance : bool = False, dynamic_origin : bool = False) -> "ParticleEffect":
        if name not in cls.effects_data:
            core_object.log(f"Particle effect '{name}' does not exist")
            return None
        effect_data : EffectData = cls.effects_data[name]
        effect_type : str = effect_data['type']
        if effect_type is None:
            return ParticleEffect(effect_data, persistance, dynamic_origin)
        special_effect_class = ParticleEffect.special_effect_name_dict.get(effect_type, SpecialParticleEffect)
        return special_effect_class(effect_data, persistance, dynamic_origin)
    
    def emit(self, track : 'ParticleEffectTrack'):
        new_particle : Particle = Particle.inactive_elements[0]

        offset = pygame.Vector2(rand_float(self.data['offset_x']), rand_float(self.data['offset_y']))
        if not self.dynamic_origin:
            new_pos = track.origin + offset
        else:
            new_pos = self.position + offset

        life = rand_float(self.data['lifetime'])
        if (self.data['velocity_x'] is None) or (self.data['velocity_y'] is None):
            velocity = None
        else:
            velocity = pygame.Vector2(rand_float(self.data['velocity_x']), rand_float(self.data['velocity_y']))
        drag = rand_float(self.data['drag'])
        accel = pygame.Vector2(rand_float(self.data['accel_x']), rand_float(self.data['accel_y']))
        kill_offscreen = self.data.get('destroy_offscreen', True)
        angle = rand_float(self.data['angle'])
        mag = rand_float(self.data['speed'])
        new_particle.spawn(new_pos, life, self.data['update_method'], self.data['main_texture'], 
                           velocity=velocity, accel=accel, drag=drag, alt_textures=self.data['alt_textures'], anim=self.data['animation'], 
                           destroy_offscreen=kill_offscreen, angle=angle, mag=mag, copy_surf = self.data['copy_surface'],
                           time_source=track.time_source)
        
        track.active.append(new_particle)
        track.total_count += 1
    
    def play(self, pos : pygame.Vector2, time_source : TimeSource|None = None) -> 'ParticleEffectTrack':
        self.started_playing_once = True
        new_track = ParticleEffectTrack(pos, self.data['cooldown'], time_source=time_source)
        self.tracks.append(new_track)
        for _ in range(self.data['init_spawn_count']):
            self.emit(new_track)
        return new_track

    def update(self):
        if len(self.tracks) <= 0 and self.is_persistent == False and self.started_playing_once == True:
            self.kill_safe()
            return
        to_del = []
        for track in self.tracks:
            self.continue_track(track)
            if track.ended: 
                to_del.append(track)

        for track in to_del:
            self.tracks.remove(track)

    def continue_track(self, track : 'ParticleEffectTrack'):
        if track.timer.isover() and track.total_count < self.data['target_spawn_count']:
            count, remainder = divmod(track.timer.get_time() , track.timer.duration)
            track.timer.restart()
            if track.can_emit:
                for _ in range(round(count)):
                    for _ in range(self.data['part_per_wave']):
                        self.emit(track)
                        if track.total_count >= self.data['target_spawn_count']: break
            track.timer.start_time -= remainder

            

        if (len(track.active) == 0) and ((track.total_count >= self.data['target_spawn_count']) or (track.can_emit == False)):
            track.ended = True
        
        to_del = []
        for part in track.active:
            if part.is_active() == False:
                to_del.append(part)

        for part in to_del:
            track.active.remove(part)

    def stop(self):
        for track in self.tracks:
            track.stop_emission()
    
    def cancel_all(self):
        for track in self.tracks:
            track.cleanup()
        self.tracks.clear()

    def kill_safe(self):
        self._zombie = True
        self.stop()
    
    def destroy(self):
        ParticleEffect.elements.remove(self)
        self.stop()
    
    @classmethod
    def update_all(cls):
        to_del : list[ParticleEffect] = []
        for element in cls.elements:
            element.update()
            if element._zombie:
                to_del.append(element)
        for element in to_del:
            cls.elements.remove(element)
    
    def shedule_destruction(self):
        self.destroy_on_end = True

class SpecialParticleEffect(ParticleEffect):
    def __init__(self, data : EffectData, persistance : bool, dynamic_origin : bool = False):
        super().__init__(data, persistance, dynamic_origin)
        self.type : str = data['type']

class TestParticleEffect(SpecialParticleEffect):
    pass

ParticleEffect.special_effect_name_dict['test'] = TestParticleEffect
class TestEffectData(EffectData):
    pass


class ParticleEffectTrack:
    def __init__(self, origin, cooldown, time_source : TimeSource|None = None) -> None:
        self.total_count = 0
        self.active : list[Particle] = []
        self.timer : Timer = Timer(cooldown, time_source)
        self.origin = origin
        self.ended = False
        self.can_emit = True
        self.time_source : TimeSource|None = time_source
    
    def cleanup(self):
        for part in self.active:
            part.kill_instance_safe()
        self.active.clear()
    
    def stop_emission(self):
        self.can_emit = False

TEMPLATE : EffectData = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [0,0], 'angle' : [0,360], 'speed' : [0,0],
            'accel_x' : [0,0], 'accel_y' : [0,0], 'drag' : [0, 0],
            'init_spawn_count' : 0, 'cooldown' : 0.25, 'target_spawn_count' : 0, 'lifetime' : [0,0], 'part_per_wave' : 1,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : False, 'type' : None}

test_effect : EffectData = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [0,0], 'angle' : [80, 100], 'speed' : [5, 9],
            'accel_x' : [0,0], 'accel_y' : [0.15,0.12], 'drag' : [0, 0],
            'init_spawn_count' : 3, 'cooldown' : 0.20, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 3,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'simulated', 'destroy_offscreen' : False, 'copy_surface' : False, 'type' : None}

test_effect2 : EffectData = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [1.5,1.6], 'velocity_y' : [0.8,0.82], 'angle' : [0, 20], 'speed' : [20, 22],
            'accel_x' : [0,0], 'accel_y' : [0.0,0.0], 'drag' : [0, 0],
            'init_spawn_count' : 1, 'cooldown' : 0.05, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 1,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : None,
            'update_method' : 'spiral', 'destroy_offscreen' : False, 'copy_surface' : False, 'type' : None
}

enemy_damaged : EffectData = {'offset_x' : [-8, 8], 'offset_y' : [0, 8], 'velocity_x' : [0,0], 'velocity_y' : [-6.0,-6.0], 'angle' : [210, 330], 'speed' : [8, 8],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 3, 'cooldown' : 0.20, 'target_spawn_count' : 3, 'lifetime' : [5,5], 'part_per_wave' : 3,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_hit_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

enemy_killed : EffectData = {'offset_x' : [-8, 8], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-3.0,-3.0], 'angle' : [0, 360], 'speed' : [5, 5],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 8, 'cooldown' : 0.20, 'target_spawn_count' : 8, 'lifetime' : [5,5], 'part_per_wave' : 8,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_killed_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

boss_killed : EffectData = {'offset_x' : [-8, 8], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-3.0,-3.0], 'angle' : [0, 360], 'speed' : [5, 5],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 35, 'cooldown' : 0.20, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 35,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('enemy_killed_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

dash_effect : EffectData = {'offset_x' : [-16, 16], 'offset_y' : [-8, 8], 'velocity_x' : [0,0], 'velocity_y' : [-1.5,-1.5], 'angle' : [0, 0], 'speed' : [0, 0],
            'accel_x' : [0,0], 'accel_y' : [-0.11,-0.10], 'drag' : [0, 0],
            'init_spawn_count' : 5, 'cooldown' : 0.025, 'target_spawn_count' : 35, 'lifetime' : [5,5], 'part_per_wave' : 5,
            'main_texture' : Particle.test_image, 'alt_textures' : None, "animation" : Animation.get_animation('dash_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

explosion_effect : EffectData = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [-2.0,-2.0], 'angle' : [0, 360], 'speed' : [3, 3],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 20, 'cooldown' : 0.20, 'target_spawn_count' : 20, 'lifetime' : [5,5], 'part_per_wave' : 20,
            'main_texture' : Particle.spark_particle_image, 'alt_textures' : None, "animation" : Animation.get_animation('explosion_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

explosion_small_effect : EffectData = {'offset_x' : [0, 0], 'offset_y' : [0, 0], 'velocity_x' : [0,0], 'velocity_y' : [-2.0,-2.0], 'angle' : [0, 360], 'speed' : [3, 3],
            'accel_x' : [0,0], 'accel_y' : [0.12,0.15], 'drag' : [0, 0],
            'init_spawn_count' : 10, 'cooldown' : 0.20, 'target_spawn_count' : 10, 'lifetime' : [5,5], 'part_per_wave' : 10,
            'main_texture' : Particle.spark_particle_image, 'alt_textures' : None, "animation" : Animation.get_animation('explosion_particle_alpha_gradient'),
            'update_method' : 'simulated', 'destroy_offscreen' : True, 'copy_surface' : True, 'type' : None
}

ParticleEffect.effects_data = {'test' : test_effect, 'test2' : test_effect2, 'enemy_damaged' : enemy_damaged,
                               'enemy_killed' : enemy_killed, 'boss_killed' : boss_killed, 'dash_effect' : dash_effect,
                               'explosion_effect' : explosion_effect, 'explosion_small_effect' : explosion_small_effect}

def runtime_imports():
    global core_object
    from framework.core.core import core_object
    Particle.bounding_box = pygame.Rect(0, 0, *core_object.main_display.get_size())
