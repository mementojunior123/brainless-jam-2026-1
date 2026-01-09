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
        self.control_script : BasicBossControlScript
        self.health_bar : UiSprite
        self.max_hp : float
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
        element.max_hp = 60
        element.health = element.max_hp
        element.health_bar = element.create_healthbar_visual()
        element.update_healthbar_visual()
        core_object.main_ui.add(element.health_bar)
        element.health_bar.visible = False
        element.invincible = False

        element.control_script = BasicBossControlScript()
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
        elif self.control_script.is_over:
            self.kill_instance_safe()
            return
        self.check_collisions()
        self.update_healthbar_visual()

    def when_hit(self, projectile : BaseProjectile):
        self.take_damage(projectile.damage)
        overlap_point : tuple[int, int] = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point)
        if self.health <= 0:
            core_object.main_ui.remove(self.health_bar)
            pass
        if not self.invincible:
            ParticleEffect.load_effect('enemy_damaged').play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx(BaseEnemy.enemy_hit_sfx, 1.0)
            self.give_score(1)

    def take_damage(self, damage : float):
        if not self.invincible:
            core_object.log(f"Basic boss took damage : {damage:.2f}")
            self.health -= damage
            self.health_bar.visible = True
    
    def fire_homing_projectile(self, angle : float = 0) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, self.rect.height // 2 + 10), pygame.Vector2(0, 8).rotate(angle), 
                                      None, None, angle,
        BaseProjectile.rocket_image, homing_range=300, homing_rate=1,
        homing_targets=Player, team=Teams.ENEMY)
    
    def fire_normal_projectile(self, angle : float = 0) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, self.rect.height // 2 + 10), pygame.Vector2(0, 8).rotate(angle), 
                                      None, None, angle,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)
    
    def clean_instance(self):
        super().clean_instance()
        self.control_script = None
        self.max_hp = None
        self.health_bar = None

class BasicBossControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, None]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        entry_script : BasicBossEntryScript = BasicBossEntryScript()
        entry_script.initialize(time_source, unit)
        delta = yield
        if delta is None: delta = core_object.dt
        while not entry_script.is_over:
            entry_script.process_frame(delta)
            delta = yield
        
        main_script : BasicBossMovementScript = BasicBossMovementScript()
        main_script2 : BasicBossShootingScript = BasicBossShootingScript()
        main_script.initialize(time_source, unit)
        main_script2.initialize(time_source, unit)
        while unit.health > 0:
            main_script.process_frame(delta)
            main_script2.process_frame(delta)
            delta = yield
        unit.invincible = True
        death_script : BasicBossDeathSequence = BasicBossDeathSequence()
        death_script.initialize(time_source, unit)
        while not death_script.is_over:
            death_script.process_frame(delta)
            delta = yield
        unit.give_score(200)
        return

class BasicBossEntryScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, str]: #Yield, Send, Return
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
        return "Done"

class BasicBossMovementScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|CoroutineScript:
        return super().process_frame(values)

    @staticmethod
    def predict_projectile_contact(unit : BasicBoss, projectile : BaseProjectile, unit_velocity : pygame.Vector2,
                                   bounding_box : pygame.Rect) -> bool:
        if abs(unit.position.y - projectile.position.y) > 200.0:
            return False
        projected_unit_position : pygame.Vector2 = unit.position.copy()
        projected_projectile_position : pygame.Vector2 = projectile.position.copy()
        projected_unit_rect = unit.rect.copy()
        projected_projectile_rect = projectile.rect.copy()
        prev_distance : float = 999_999.0
        for _ in range(100):
            projected_unit_position += unit_velocity
            projected_projectile_position += projectile.velocity
            projected_projectile_rect.center = projected_projectile_position
            projected_unit_rect.center = projected_unit_position
            distance : float = (projected_projectile_position - projected_unit_position).magnitude()
            if projected_projectile_rect.colliderect(projected_unit_rect):
                return True
            prev_distance = distance
            if not (bounding_box.collidepoint(projected_unit_position) and bounding_box.collidepoint(projected_projectile_position)):
                break
        return False

    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, CoroutineScript]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        dodge_cooldown : Timer = Timer(0.5, time_source)
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)
        direction : int = 1
        SPEED : float = 6.0
        move_timer : Timer = Timer(-1, time_source)
    
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, SPEED, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            distance_to_margin : float = min(unit.rect.left, abs(screen_sizex - unit.rect.right))
            if distance_to_margin > 50:
                if dodge_cooldown.isover():
                    for proj in BaseProjectile.active_elements:
                        if proj.team not in (Teams.ALLIED, Teams.FFA):
                            continue
                        if BasicBossMovementScript.predict_projectile_contact(
                        unit, proj, pygame.Vector2(direction * SPEED, 0), bounding_box):
                            dodge_cooldown.set_duration(0.5 if distance_to_margin > 200 else 1.0 )
                            if distance_to_margin < 100:
                                luck = 5
                            else:
                                luck = 8
                            if random.randint(1, 10) <= luck:
                                direction *= -1
            delta = yield

class BasicBossShootingScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 8
        elif x_offset < 50:
            return 4
        elif x_offset < 100:
            return 2
        elif x_offset < 150:
            return 1
        else:
            return 0.5
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        min_shot_cooldown : Timer = Timer(0.25, time_source)
        aggro_required : float = 90.0
        current_aggro : float = 0
        player : Player|None
        if not Player.active_elements:
            player = None
        else:
            player = Player.active_elements[0]
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            proximity_buff : float = BasicBossShootingScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position)) * 0
                unit.fire_normal_projectile(angle_offset)
                shotgun_odds : int = 1 if angle_offset < 10 else 2
                fired_shotgun : bool = random.randint(1, 4) <= shotgun_odds
                if fired_shotgun:
                    unit.fire_normal_projectile(angle_offset - 20)
                    unit.fire_normal_projectile(angle_offset + 20)
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(40, 80) if not fired_shotgun else random.uniform(60, 120)
            delta = yield

class BasicBossDeathSequence(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : BasicBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : BasicBoss) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        delta = yield
        if delta is None: delta = core_object.dt
        #Insert death sequence
        ParticleEffect.load_effect('boss_killed').play(unit.position.copy(), core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx(BaseEnemy.enemy_killed_sfx, 1.0)
        return "Done"

class GoldenBoss(BaseBoss):
    active_elements : list['GoldenBoss'] = []
    inactive_elements : list['GoldenBoss'] = []
    linked_classes : list['Sprite'] = [Sprite, BaseEnemy, BaseBoss]

    golden_boss_image : pygame.Surface = pygame.transform.scale_by(load_alpha_to_colorkey('assets/graphics/enemy/elite_enemy.png', 
                                                                                         (0, 255, 0)), 2)
    def __init__(self):
        super().__init__()
        self.control_script : GoldenBossControlScript
        self.health_bar : UiSprite
        self.max_hp : float
        GoldenBoss.inactive_elements.append(self)

    @classmethod
    def spawn(cls):
        element = cls.inactive_elements[0]

        element.image = GoldenBoss.golden_boss_image
        element.mask = pygame.mask.from_surface(element.image)
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect("midbottom", pygame.Vector2(480, 0))
        element.zindex = 0
        element.current_camera = core_object.game.main_camera

        element.type = 'golden_boss'
        element.max_hp = 150
        element.health = element.max_hp
        element.health_bar = element.create_healthbar_visual()
        element.update_healthbar_visual()
        core_object.main_ui.add(element.health_bar)
        element.health_bar.visible = False
        element.invincible = False

        element.control_script = GoldenBossControlScript()
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
        elif self.control_script.is_over:
            self.kill_instance_safe()
            return
        self.check_collisions()
        self.update_healthbar_visual()

    def when_hit(self, projectile : BaseProjectile):
        self.take_damage(projectile.damage)
        overlap_point : tuple[int, int] = self.mask.overlap(projectile.mask, (projectile.rect.x - self.rect.x, projectile.rect.y - self.rect.y))
        point_of_contact : pygame.Vector2 = (pygame.Vector2(self.rect.topleft) + overlap_point)
        if self.health <= 0:
            core_object.main_ui.remove(self.health_bar)
            pass
        if not self.invincible:
            ParticleEffect.load_effect('enemy_damaged').play(point_of_contact, core_object.game.game_timer.get_time)
            core_object.bg_manager.play_sfx(BaseEnemy.enemy_hit_sfx, 1.0)
            self.give_score(1)

    def take_damage(self, damage : float):
        if not self.invincible:
            core_object.log(f"Basic boss took damage : {damage:.2f}")
            self.health -= damage
            self.health_bar.visible = True
    
    def fire_homing_projectile(self, angle : float = 0, speed : float = 4.5, rate : float = 0.8, h_range : float = 300) -> HomingProjectile:
        return HomingProjectile.spawn(self.position + pygame.Vector2(0, self.rect.height // 2 - 15), 
                                      pygame.Vector2(0, speed).rotate(angle), 
                                      None, None, 0,
        BaseProjectile.rocket_image, homing_range=h_range, homing_rate=rate,
        homing_targets=Player, team=Teams.ENEMY, destructible=True)
    
    def fire_normal_projectile(self, angle : float = 0) -> NormalProjectile:
        return NormalProjectile.spawn(self.position + pygame.Vector2(0, self.rect.height // 2 + 10), pygame.Vector2(0, 8).rotate(angle), 
                                      None, None, 0,
        recolor_image(BaseProjectile.normal_image3, "Red"),  team=Teams.ENEMY)
    
    def clean_instance(self):
        super().clean_instance()
        self.control_script = None
        self.max_hp = None
        self.health_bar = None

class GoldenBossControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, None]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        entry_script : GoldenBossEntryScript = GoldenBossEntryScript()
        entry_script.initialize(time_source, unit)
        delta = yield
        if delta is None: delta = core_object.dt
        while not entry_script.is_over:
            entry_script.process_frame(delta)
            delta = yield
        
        main_script : GoldenBossMovementScript = GoldenBossMovementScript()
        main_script2 : GoldenBossShootingScript = GoldenBossShootingScript()
        main_script3 : GoldenBossHomingShotScript = GoldenBossHomingShotScript()
        main_script.initialize(time_source, unit)
        main_script2.initialize(time_source, unit)
        main_script3.initialize(time_source, unit)
        while unit.health > 0:
            main_script.process_frame(delta)
            main_script2.process_frame(delta)
            main_script3.process_frame(delta)
            delta = yield
        unit.invincible = True
        death_script : GoldenBossDeathSequence = GoldenBossDeathSequence()
        death_script.initialize(time_source, unit)
        while not death_script.is_over:
            death_script.process_frame(delta)
            delta = yield
        unit.give_score(200)
        return

class GoldenBossEntryScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, str]: #Yield, Send, Return
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
        return "Done"

class GoldenBossMovementScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|CoroutineScript:
        return super().process_frame(values)

    @staticmethod
    def predict_projectile_contact(unit : GoldenBoss, projectile : BaseProjectile, unit_velocity : pygame.Vector2,
                                   bounding_box : pygame.Rect) -> bool:
        if abs(unit.position.y - projectile.position.y) > 200.0:
            return False
        projected_unit_position : pygame.Vector2 = unit.position.copy()
        projected_projectile_position : pygame.Vector2 = projectile.position.copy()
        projected_unit_rect = unit.rect.copy()
        projected_projectile_rect = projectile.rect.copy()
        prev_distance : float = 999_999.0
        for _ in range(100):
            projected_unit_position += unit_velocity
            projected_projectile_position += projectile.velocity
            projected_projectile_rect.center = projected_projectile_position
            projected_unit_rect.center = projected_unit_position
            distance : float = (projected_projectile_position - projected_unit_position).magnitude()
            if projected_projectile_rect.colliderect(projected_unit_rect):
                return True
            prev_distance = distance
            if not (bounding_box.collidepoint(projected_unit_position) and bounding_box.collidepoint(projected_projectile_position)):
                break
        return False

    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, CoroutineScript]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        dodge_cooldown : Timer = Timer(0.5, time_source)
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)
        direction : int = 1
        SPEED : float = 6.0
        move_timer : Timer = Timer(-1, time_source)
    
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            speed_percent = interpolation.quad_ease_out(pygame.math.clamp(move_timer.get_time() / 0.3, 0, 1))
            actual_speed = pygame.math.lerp(0, SPEED, speed_percent)
            unit.position += pygame.Vector2(direction * actual_speed * delta, 0)
            if unit.rect.right > screen_sizex: 
                unit.move_rect("right", screen_sizex)
                direction = -1
            if unit.rect.left < 0: 
                unit.move_rect("left", 0)
                direction = 1
            distance_to_margin : float = min(unit.rect.left, abs(screen_sizex - unit.rect.right))
            if distance_to_margin > 50:
                if dodge_cooldown.isover():
                    for proj in BaseProjectile.active_elements:
                        if proj.team not in (Teams.ALLIED, Teams.FFA):
                            continue
                        if GoldenBossMovementScript.predict_projectile_contact(
                        unit, proj, pygame.Vector2(direction * SPEED, 0), bounding_box):
                            dodge_cooldown.set_duration(0.5 if distance_to_margin > 200 else 0.75 )
                            if distance_to_margin < 100:
                                luck = 6
                            else:
                                luck = 8
                            if random.randint(1, 10) <= luck:
                                direction *= -1
            delta = yield

class GoldenBossShootingScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 8
        elif x_offset < 50:
            return 4
        elif x_offset < 100:
            return 2
        elif x_offset < 150:
            return 1
        else:
            return 0.5
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        min_shot_cooldown : Timer = Timer(0.25, time_source)
        aggro_required : float = 90.0
        current_aggro : float = 0
        player : Player|None
        if not Player.active_elements:
            player = None
        else:
            player = Player.active_elements[0]
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            proximity_buff : float = GoldenBossShootingScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position))
                unit.fire_normal_projectile()
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(30, 60)
            delta = yield

class GoldenBossHomingShotScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def player_proximity_buff(x_offset : float) -> float:
        if x_offset < 16:
            return 2
        elif x_offset < 50:
            return 1.5
        elif x_offset < 100:
            return 1
        elif x_offset < 150:
            return 0.8
        else:
            return 0.8
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        min_shot_cooldown : Timer = Timer(0.25, time_source)
        aggro_required : float = 200.0
        current_aggro : float = 0
        player : Player|None
        if not Player.active_elements:
            player = None
        else:
            player = Player.active_elements[0]
        delta = yield
        if delta is None: delta = core_object.dt
        while True:
            proximity_buff : float = GoldenBossShootingScript.player_proximity_buff(abs(unit.position.x - player.position.x) if player else 999)
            current_aggro +=  delta * proximity_buff
            if min_shot_cooldown.isover() and current_aggro >= aggro_required:
                angle_offset : float = (pygame.Vector2(0, 1).angle_to(player.position - unit.position))

                unit.fire_homing_projectile(angle=angle_offset - 30)
                unit.fire_homing_projectile(angle=angle_offset + 30)
                min_shot_cooldown.restart()
                current_aggro = 0
                aggro_required = random.uniform(90, 270)
            delta = yield

class GoldenBossDeathSequence(CoroutineScript):
    def initialize(self, time_source : TimeSource, unit : GoldenBoss):
        return super().initialize(time_source, unit)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, unit : GoldenBoss) -> Generator[None, float, str]: #Yield, Send, Return
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2
        bounding_box : pygame.Rect = pygame.Rect(0, 0, screen_sizex, screen_sizey)

        delta = yield
        if delta is None: delta = core_object.dt
        #Insert death sequence
        ParticleEffect.load_effect('boss_killed').play(unit.position.copy(), core_object.game.game_timer.get_time)
        core_object.bg_manager.play_sfx(BaseEnemy.enemy_killed_sfx, 1.0)
        return "Done"

def runtime_imports():
    global Player, src
    from src.sprites.player import Player
    import src.sprites.player

Sprite.register_class(BaseBoss)
Sprite.register_class(BaseMiniboss)

Sprite.register_class(BasicBoss)
Sprite.register_class(GoldenBoss)
for _ in range(2): BasicBoss()
for _ in range(2) : GoldenBoss()