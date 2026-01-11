import pygame
from typing import Any, Generator, TypedDict, Literal, Union
from math import floor, sin, pi
from enum import Enum
from random import shuffle, choice, choices
import random
import framework.game.coroutine_scripts
from framework.game.coroutine_scripts import CoroutineScript
import framework.utils.tween_module as TweenModule
from framework.utils.ui.ui_sprite import UiSprite
from framework.utils.ui.textbox import TextBox
from framework.utils.ui.textsprite import TextSprite
from framework.utils.ui.base_ui_elements import BaseUiElements
import framework.utils.interpolation as interpolation
from framework.utils.my_timer import Timer, TimeSource
from framework.game.sprite import Sprite
from framework.utils.helpers import average, random_float, ColorType
from framework.utils.ui.brightness_overlay import BrightnessOverlay
from framework.utils.particle_effects import ParticleEffect, Particle

class GameState:
    def __init__(self, game_object : 'Game'):
        self.game = game_object

    def main_logic(self, delta : float):
        pass

    def pause(self):
        pass

    def unpause(self):
        pass

    def handle_key_event(self, event : pygame.Event):
        pass

    def handle_mouse_event(self, event : pygame.Event):
        pass

    def cleanup(self):
        pass

class NormalGameState(GameState):
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)

    def pause(self):
        if not self.game.active: return
        self.game.game_timer.pause()
        window_size = core_object.main_display.get_size()
        pause_ui1 = BrightnessOverlay(-60, pygame.Rect(0,0, *window_size), 0, 'pause_overlay', zindex=999)
        pause_ui2 = TextSprite(pygame.Vector2(window_size[0] // 2, window_size[1] // 2), 'center', 0, 'Paused', 'pause_text', None, None, 1000,
                               (self.game.font_70, 'White', False), ('Black', 2), colorkey=(0, 255, 0))
        core_object.main_ui.add(pause_ui1)
        core_object.main_ui.add(pause_ui2)
        self.game.state = PausedGameState(self.game, self)
    
    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.pause()

class WaveData(TypedDict):
    enemies : dict[Union["EnemyType", "BossType"], int]
    spawn_cooldown : float
    spawn_rate_penalty_per_enemy : float
    bosses : list["BossType"]

WAVE_DATA : dict[int, WaveData] = {
    1 : {
        'enemies' : {
            'basic' : 5,
        },
        "spawn_cooldown" : 2.9,
        "spawn_rate_penalty_per_enemy" : 1.2,
        'bosses' : []
    },

    2 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 1,
            'gunner' : 1,
        },
        "spawn_cooldown" : 2.7,
        "spawn_rate_penalty_per_enemy" : 1.2,
        'bosses' : []
    },

    3 : {
        'enemies' : {
            'basic' : 5,
            'elite' : 3,
            'gunner' : 2,
            'runner' : 1,
        },
        "spawn_cooldown" : 2.6,
        "spawn_rate_penalty_per_enemy" : 1.2,
        'bosses' : []
    },

    4 : {
        'enemies' : {
            'basic' : 6,
            'elite' : 5,
            'gunner' : 3,
            'runner' : 1
        },
        "spawn_cooldown" : 2.5,
        "spawn_rate_penalty_per_enemy" : 1.1,
        'bosses' : []
    },

    5 : {
        'enemies' : {
            'basic' : 6,
            'elite' : 6,
            'gunner' : 4,
            'runner' : 2
        },
        "spawn_cooldown" : 2.4,
        "spawn_rate_penalty_per_enemy" : 1.1,
        'bosses' : ['basic_boss']
    },

    6 : {
        'enemies' : {
            'basic' : 7,
            'elite' : 7,
            'gunner' : 4,
            'runner' : 2
        },
        "spawn_cooldown" : 2.2,
        "spawn_rate_penalty_per_enemy" : 1.0,
        'bosses' : []
    },

    7 : {
        'enemies' : {
            'basic' : 5,
            'elite' : 9,
            'gunner' : 5,
            'runner' : 3,
        },
        "spawn_cooldown" : 2.1,
        "spawn_rate_penalty_per_enemy" : 0.9,
        'bosses' : []
    },

    8 : {
        'enemies' : {
            'basic' : 5,
            'elite' : 10,
            'gunner' : 5,
            'runner' : 3,
        },
        "spawn_cooldown" : 2.0,
        "spawn_rate_penalty_per_enemy" : 0.8,
        'bosses' : []
    },

    9 : {
        'enemies' : {
            'basic' : 6,
            'elite' : 12,
            'gunner' : 5,
            'runner' : 3,
        },
        "spawn_cooldown" : 1.9,
        "spawn_rate_penalty_per_enemy" : 0.7,
        'bosses' : []
    },

    10 : {
        'enemies' : {
            'basic' : 7,
            'elite' : 13,
            'gunner' : 6,
            'runner' : 4,
        },
        "spawn_cooldown" : 1.8,
        "spawn_rate_penalty_per_enemy" : 0.6,
        'bosses' : ['golden_boss']
    },

    11 : {
        'enemies' : {
            'basic' : 8,
            'elite' : 16,
            'gunner' : 8,
            'runner' : 4,
            'basic_boss' : 1
            
        },
        "spawn_cooldown" : 1.6,
        "spawn_rate_penalty_per_enemy" : 0.5,
        'bosses' : []
    },

    12 : {
        'enemies' : {
            'basic' : 9,
            'elite' : 18,
            'gunner' : 9,
            'runner' : 5,
            'basic_boss' : 2
        },
        "spawn_cooldown" : 1.5,
        "spawn_rate_penalty_per_enemy" : 0.5,
        'bosses' : []
    },


    13 : {
        'enemies' : {
            'basic' : 10,
            'elite' : 20,
            'gunner' : 10,
            'runner' : 5,
            'golden_boss' : 1
        },
        "spawn_cooldown" : 1.4,
        "spawn_rate_penalty_per_enemy" : 0.4,
        'bosses' : []
    },


    14 : {
        'enemies' : {
            'basic' : 11,
            'elite' : 22,
            'gunner' : 11,
            'runner' : 5,
            'golden_boss' : 1
        },
        "spawn_cooldown" : 1.3,
        "spawn_rate_penalty_per_enemy" : 0.3,
        'bosses' : []
    },

    15 : {
        'enemies' : {
            'basic' : 12,
            'elite' : 24,
            'gunner' : 12,
            'runner' : 6,
            'basic_boss' : 1,
            'golden_boss' : 1
        },
        "spawn_cooldown" : 1.3,
        "spawn_rate_penalty_per_enemy" : 0.2,
        'bosses' : ['spaceship_boss']
    },

        16 : {
        'enemies' : {
            'basic' : 15,
            'elite' : 30,
            'gunner' : 15,
            'runner' : 7,
            'basic_boss' : 1,
            'golden_boss' : 1,
        },
        "spawn_cooldown" : 1.2,
        "spawn_rate_penalty_per_enemy" : 0.15,
        'bosses' : []
    },

    17 : {
        'enemies' : {
            'basic' : 17,
            'elite' : 34,
            'gunner' : 17,
            'runner' : 8,
            'basic_boss' : 2,
            'golden_boss' : 1,
        },
        "spawn_cooldown" : 1.2,
        "spawn_rate_penalty_per_enemy" : 0.15,
        'bosses' : []
    },


    18 : {
        'enemies' : {
            'basic' : 18,
            'elite' : 36,
            'gunner' : 18,
            'runner' : 9,
            'basic_boss' : 2,
            'golden_boss' : 2,
        },
        "spawn_cooldown" : 1.1,
        "spawn_rate_penalty_per_enemy" : 0.15,
        'bosses' : []
    },


    19 : {
        'enemies' : {
            'basic' : 21,
            'elite' : 42,
            'gunner' : 21,
            'runner' : 10,
            'basic_boss' : 2,
            'golden_boss' : 2,
        },
        "spawn_cooldown" : 1.1,
        "spawn_rate_penalty_per_enemy" : 0.1,
        'bosses' : []
    },

    20 : {
        'enemies' : {
            'basic' : 20,
            'elite' : 48,
            'gunner' : 24,
            'runner' : 12,
            'basic_boss' : 3,
            'golden_boss' : 2,
        },
        "spawn_cooldown" : 1.0,
        "spawn_rate_penalty_per_enemy" : 0.08,
        'bosses' : ['final_boss']
    },
}

SCORE_EVENT = pygame.event.custom_type()

class MainGameState(NormalGameState):
    main_theme : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/music/theme2_trimmed_good.ogg")
    main_theme.set_volume(0.2)

    boss_theme : pygame.mixer.Sound = pygame.mixer.Sound("assets/audio/music/theme1.ogg")
    boss_theme.set_volume(0.2)

    @property
    def score(self):
        return self._score
    
    @score.setter
    def score(self, new_val : int):
        self._score = new_val
        self.score_sprite.text = f"Score : {self._score}"

    def __init__(self, game_object : "Game", prev_main_state : Union["MainGameState", None] = None, wave_num : int = 1):
        self.game : Game = game_object
        self.player : Player
        self.screen_size : tuple[int, int]
        self.score_sprite : TextSprite
        self._score : int
        if prev_main_state is None:
            self.spawn_background()
            core_object.fps_sprite.visible = False
            self.player = Player.spawn("midbottom", pygame.Vector2(480, 520))
            self.screen_size = core_object.main_display.get_size()
            self.score_sprite = TextSprite(pygame.Vector2(15, 10), 'topleft', 0, 'Score : 0', 'fps_sprite', 
                            text_settings=(self.game.font_40, 'White', False), text_stroke_settings=('Black', 2),
                            colorkey=(255, 0,0))
            core_object.main_ui.add(self.score_sprite)
            self._score = 0
            core_object.bg_manager.play(self.main_theme, 1.0)
            ShopControlScript.update_music_volume(1.0)
            src.sprites.player.make_connections()
        else:
            self.player = prev_main_state.player
            self.screen_size = prev_main_state.screen_size
            self.score_sprite = prev_main_state.score_sprite
            self._score = prev_main_state._score
            core_object.event_manager.unbind(SCORE_EVENT, prev_main_state.handle_score_event)
        
        self.control_script : BasicWaveControlScript = BasicWaveControlScript()
        self.control_script.initialize(self.game.game_timer.get_time, wave_num)
        core_object.event_manager.bind(SCORE_EVENT, self.handle_score_event)

        self.wave_number : int = wave_num
        self.game.alert_player(f"Wave {self.wave_number} start")
        if not core_object.bg_manager.get_all_type("Music"):
            core_object.bg_manager.play(self.main_theme, 1.0, fade_ms=2000)
    
    def handle_score_event(self, event : pygame.Event):
        if event.type == SCORE_EVENT:
            self.score += event.score

    def spawn_background(self):
        bg = Background.spawn(core_object.main_display.get_size()[1])
        while True:
            if bg.rect.top > 0:
                bg = Background.spawn(bg.rect.top)
            else:
                break

    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
        self.control_script.process_frame(delta)
        if self.player.current_hp <= 0:
            self.transition_to_gameover()
        if self.control_script.is_over:
            if self.wave_number >= 20:
                self.trasition_to_win()
            else:
                self.transition_to_shop()
        

    def transition_to_gameover(self):
        self.game.state = GameOverGameState(self.game, prev_state=self)
    
    def trasition_to_win(self):
        self.game.state = GameOverGameState(self.game, "You win!", prev_state=self)
    
    def transition_to_shop(self):
        self.game.state = ShopGameState(self.game, self.wave_number, self)
    

    def cleanup(self):
        if self.score > core_object.storage.high_score:
            core_object.storage.high_score = self.score
            core_object.storage.save(core_object.is_web())
        super().cleanup()
        src.sprites.player.remove_connections()
        core_object.bg_manager.stop_all_music()
        core_object.event_manager.unbind(SCORE_EVENT, self.handle_score_event)


class MainControlScipt(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, float, str]:
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        timer : Timer = Timer(-1, time_source)
        delta : float = yield
        wave1_script : BasicWaveControlScript = BasicWaveControlScript()
        wave1_script.initialize(time_source, 1)
        if delta is None: delta = core_object.dt
        while True:
            wave1_script.process_frame(delta)
            if wave1_script.is_over:
                break
            delta = yield
        return "Done"

class BasicWaveControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, wave_number : int):
        return super().initialize(time_source, wave_number)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def pick_random_enemy(enemy_dict : dict[str, int]) -> str:
        return choices(list(enemy_dict.keys()), list(enemy_dict.values()))[0]
    
    @staticmethod
    def spawn_enemy(enemy_type : Union["EnemyType", "BossType"], x_level : int):
        if enemy_type == EnemyTypes.BASIC.value:
            BasicEnemy.spawn("midbottom", pygame.Vector2(x_level, -20))
        elif enemy_type == EnemyTypes.ELITE.value:
            EliteEnemy.spawn("midbottom", pygame.Vector2(x_level, -20))
        elif enemy_type == EnemyTypes.GUNNER.value:
            GunnerEnemy.spawn("midbottom", pygame.Vector2(x_level, -20))
        elif enemy_type == EnemyTypes.RUNNER.value:
            RunnerEnemy.spawn("midbottom", pygame.Vector2(x_level, -20))
        elif enemy_type == BossTypes.BASIC_BOSS.value:
            boss = BasicBoss.spawn()
            boss.max_hp = boss.max_hp // 1.5
            boss.health = boss.max_hp
        elif enemy_type == BossTypes.GOLDEN_BOSS.value:
            boss = GoldenBoss.spawn()
            boss.max_hp = boss.max_hp // 2
            boss.health = boss.max_hp
        elif enemy_type == BossTypes.SPACESHIP_BOSS.value:
            boss = SpaceshipBoss.spawn()
            boss.max_hp = boss.max_hp // 3
            boss.health = boss.max_hp
        elif enemy_type == BossTypes.FINAL_BOSS.value:
            boss = SpaceshipBoss.spawn()
            boss.max_hp = boss.max_hp // 3
            boss.health = boss.max_hp
        else:
            core_object.log(f"Enemy type '{enemy_type}' not found!")
    
    @staticmethod
    def spawn_boss(boss_type : "BossType") -> "BaseBoss":
        core_object.game.alert_player("Boss incoming!")
        if boss_type == "basic_boss":
            return BasicBoss.spawn()
        elif boss_type == 'golden_boss':
            return GoldenBoss.spawn()
        elif boss_type == 'spaceship_boss':
            return SpaceshipBoss.spawn()
        elif boss_type == 'final_boss':
            return FinalBoss.spawn()
        else:
            core_object.log(f"Enemy type '{boss_type}' not found")
    
    @staticmethod
    def corou(time_source : TimeSource, wave_number : int) -> Generator[None, float, str]:
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        wave_data : WaveData = WAVE_DATA[wave_number]
        enemies : dict[EnemyType|BossType, int] = wave_data["enemies"].copy()
        spawn_cooldown : float = wave_data["spawn_cooldown"]
        spawn_rate_penalty_per_enemy : float = wave_data["spawn_rate_penalty_per_enemy"]
        bosses : list[BossType] = wave_data['bosses'].copy()

        enemy_spawn_timer : Timer = Timer(1.5, time_source)
        wave_timer : Timer = Timer(-1, time_source)
        delta : float = yield
        if delta is None: delta = core_object.dt
        while any(enemies[k] > 0 for k in enemies):
            if enemy_spawn_timer.isover():
                enemy_spawn_timer.set_duration(spawn_cooldown + spawn_rate_penalty_per_enemy * len(BaseEnemy.active_elements))
                enemy_type_chosen : EnemyType|BossType = BasicWaveControlScript.pick_random_enemy(enemies)
                enemies[enemy_type_chosen] -= 1
                BasicWaveControlScript.spawn_enemy(enemy_type_chosen, random.randint(100, screen_sizex - 100))
            if pygame.key.get_pressed()[pygame.K_CAPSLOCK]:
                if pygame.key.get_pressed()[pygame.K_l]:
                    bosses.clear()
                if pygame.key.get_pressed()[pygame.K_o]:    
                    enemies.clear()
            delta = yield
        while BaseEnemy.active_elements:
            delta = yield
        boss_fadein_timer = None
        if bosses:
            boss_delay_timer : Timer = Timer(2, time_source)
            while not boss_delay_timer.isover():
                new_vol = pygame.math.lerp(1.0, 0.0, (boss_delay_timer.get_time() * 2) / boss_delay_timer.duration)
                ShopControlScript.update_music_volume(new_vol)
                delta = yield
            core_object.bg_manager.stop_all_music()
            ShopControlScript.update_music_volume(1.0)
            boss_fadein_timer : Timer = Timer(4, time_source)
            core_object.bg_manager.play(MainGameState.boss_theme, 1.0)
            active_boss : BaseBoss = BasicWaveControlScript.spawn_boss(bosses[0])
            bosses.pop(0)
            while bosses:
                if not active_boss.active:
                    active_boss : BaseBoss = BasicWaveControlScript.spawn_boss(bosses[0])
                    bosses.pop(0)
                ShopControlScript.update_music_volume(
                    pygame.math.lerp(0, 1, boss_fadein_timer.get_time() / boss_fadein_timer.duration))
                delta = yield
        while BaseEnemy.active_elements:
            if boss_fadein_timer:
                ShopControlScript.update_music_volume(
                    pygame.math.lerp(0, 1, boss_fadein_timer.get_time() / boss_fadein_timer.duration))
            delta = yield
        if boss_fadein_timer:
            boss_fadein_timer.set_duration(2)
            while not boss_fadein_timer.isover():
                ShopControlScript.update_music_volume(
                    pygame.math.lerp(1, 0, interpolation.quad_ease_out(boss_fadein_timer.get_time() / boss_fadein_timer.duration)))
                delta = yield
            core_object.bg_manager.stop_all_music()
            ShopControlScript.update_music_volume(1.0)
            if Player.active_elements:
                ply = Player.active_elements[0]
                ply.current_hp = ply.max_hp
        return "Done"

class ShopGameState(NormalGameState):
    def __init__(self, game_object : "Game", finished_wave : int, prev : "MainGameState"):
        self.game : "Game" = game_object
        self.prev : MainGameState = prev
        self.finished_wave : int = finished_wave
        self.control_script : ShopControlScript = ShopControlScript()
        self.candidates : dict["UpgradeType", float|int] = self.pick_candidates()
        self.major_upgrade : bool = True if self.finished_wave % 5 == 0 else False
        self.control_script.initialize(self.game.game_timer.get_time, self.candidates, self.prev.player, self)
        self.game.alert_player("Shop entered!")
    
    @staticmethod
    def get_specialist_type(player : "Player") -> "UpgradeType":
        match player.upgrades['AlternateFireType']:
            case AlternateFireTypes.LAZER.value:
                return 'LazerSpecialist'
            case AlternateFireTypes.SHOTGUN.value:
                return 'ShotgunSpecialist'
            case AlternateFireTypes.ROCKET.value:
                return 'RocketSpecialist'
            case _:
                core_object.log(f"Alternate fire type {player.upgrades['AlternateFireType']} does not exsist!")
                return None

    def pick_candidates(self, count : int = 3) -> dict["UpgradeType", float|int]:
        candidates : dict[UpgradeType, float|int]
        section : int = (self.finished_wave - 1) // 5
        if self.finished_wave % 5 != 0:
            candidates = {
                'RegularDamageBonus' : [0.4, 0.4, 0.4, 0.4][section],
                'SpecialDamageMultipler' : [0.3, 0.3, 0.3, 0.3][section],
                'AllDamageMultiplier' : [0.15, 0.15, 0.15, 0.15][section],

                'RegularFirerateMultiplier' : [0.2, 0.2, 0.2, 0.2][section],
                'SpecialFirerateMultiplier' : [0.2, 0.2, 0.2, 0.2][section],
                'AllFirerateMultiplier' : [0.1, 0.1, 0.1, 0.1][section],

                'MaxHealthBonus' : 1,
                'HealHealth' : [2, 2, 3, 3][section],
                'DashRechargeRate' : 0.25,
            }
        else:
            specialist_type : UpgradeType = self.get_specialist_type(self.prev.player)
            if section == 0:
                candidates = {
                    random.choice(['AllDamageMultiplier', 'AllFirerateMultiplier']) : 0.5,
                    'AlternateFireType' : AlternateFireTypes.SHOTGUN.value,
                    specialist_type : 1,
                }
            elif section == 1:
                candidates = {
                    random.choice(['AllDamageMultiplier', 'AllFirerateMultiplier']) : 0.5,
                    'AlternateFireType' : AlternateFireTypes.ROCKET.value,
                    specialist_type : 1,
                }
            elif section == 2:
                candidates = {
                    'AllDamageMultiplier' : 0.5,
                    'AllFirerateMultiplier' : 0.5,
                    specialist_type : 1
                }
            elif section == 3:
                core_object.log("An error has occured!")
                candidates = {
                    'AllDamageMultiplier' : 0.5,
                    'AllFirerateMultiplier' : 0.5,
                    'MaxHealthBonus' : 2,
                }
        if self.prev.player.current_hp == self.prev.player.max_hp:
            if 'HealHealth' in candidates:
                candidates.pop('HealHealth')
            if 'HealMax' in candidates:
                candidates.pop('HealMax')
        amount_chosen : int = min(count, len(candidates))
        candidate_list : list[UpgradeType] = list(candidates.keys())
        random.shuffle(candidate_list)
        chosen : list[UpgradeType] = candidate_list[:amount_chosen]
        return {upgrade : candidates[upgrade] for upgrade in chosen}

    def apply_upgrade(self, upgrade_type : "UpgradeType"):
        if upgrade_type is None:
            core_object.log("Did not apply an upgrade")
            return
        upgrade_value : float|int = self.candidates[upgrade_type]
        player : Player = self.prev.player
        match upgrade_type:
            case 'AllDamageMultiplier':
                player.upgrades[upgrade_type] += upgrade_value
            case 'AllFirerateMultiplier':
                player.upgrades[upgrade_type] += upgrade_value
            case 'AlternateFireType':
                player.upgrades['AlternateFireType'] = upgrade_value
                player.upgrades['AlternateFireBaseDamage'] = src.sprites.player.alternate_fire_base_stats[upgrade_value]['damage']
                player.upgrades['AlternateFireBaseFireRate'] = src.sprites.player.alternate_fire_base_stats[upgrade_value]['firerate']
            case 'HealHealth':
                player.current_hp += upgrade_value
                if player.current_hp > player.max_hp:
                    player.current_hp = player.max_hp
            case 'HealMax':
                player.current_hp = player.max_hp
            case 'DashRechargeRate':
                player.upgrades['DashRechargeRate'] += upgrade_value
            case 'MaxHealthBonus':
                player.upgrades['MaxHealthBonus'] += upgrade_value
                prev_max_hp : int = player.max_hp
                player.max_hp = Player.BASE_HEALTH + player.upgrades['MaxHealthBonus']
                player.current_hp += (player.max_hp - prev_max_hp)
            case 'RegularDamageBonus':
                player.upgrades[upgrade_type] += upgrade_value
            case 'RegularFirerateMultiplier':
                player.upgrades[upgrade_type] += upgrade_value
            case 'SpecialDamageMultipler':
                player.upgrades[upgrade_type] += upgrade_value
            case 'SpecialFirerateMultiplier':
                player.upgrades[upgrade_type] += upgrade_value
            case 'LazerSpecialist'|'RocketSpecialist'|'ShotgunSpecialist':
                player.upgrades[upgrade_type] += upgrade_value
            case _:
                player.upgrades[upgrade_type] += upgrade_value
                core_object.log(f"Could not apply upgrade - {upgrade_type}: {upgrade_value}")
                return

        core_object.log(f"Applied upgrade - {upgrade_type}: {upgrade_value}")
            
    
    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
        self.control_script.process_frame(delta)
        if self.control_script.is_over:
            self.transition_to_main()
    
    def transition_to_main(self):
        self.game.state = MainGameState(self.game, self.prev, self.finished_wave + 1)
    
    def cleanup(self):
        self.prev.cleanup()

class ShopControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, upgrades : dict["UpgradeType", float|int], player : "Player",
                   game_state : ShopGameState):
        return super().initialize(time_source, upgrades, player, game_state)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> Union[None, "UpgradeType"]:
        return super().process_frame(values)

    @staticmethod
    def update_music_volume(new_volume : float):
        for channel in core_object.bg_manager.get_all_type('Music'):
            channel.set_volume(core_object.bg_manager.global_volume * new_volume * core_object.bg_manager.current[channel].volume)
    
    @staticmethod
    def generate_x_positions(nb : int, centerx : int) -> list[int]:
        GAP : int = 60 + UpgradeCard.default_image.get_size()[0]
        result : list[int] = []
        if nb % 2 == 1:
            result.append(centerx)
            for dx in range((nb - 1) // 2):
                result.append(centerx - GAP * dx - GAP)
                result.append(centerx + GAP * dx + GAP)
        else:
            for dx in range(nb // 2):
                result.append(centerx - GAP * dx - GAP // 2)
                result.append(centerx + GAP * dx + GAP // 2)
        return result
    
    @staticmethod
    def get_improvement_text(upgrade_type : "UpgradeType", upgrade_value : int|float, player : "Player") -> str:
        match upgrade_type:
            case 'AllDamageMultiplier': 
                old_normal_damage : float = player.get_normal_damage()
                old_special_damage : float = player.get_special_damage()
                player.upgrades['AllDamageMultiplier'] += upgrade_value
                new_normal_damage : float = player.get_normal_damage()
                new_special_damage : float = player.get_special_damage()
                player.upgrades['AllDamageMultiplier'] -= upgrade_value
                return f"{old_normal_damage:.2f} --> {new_normal_damage:.2f} dmg\n{old_special_damage:.2f} --> {new_special_damage:.2f} special dmg"
            case 'AllFirerateMultiplier':
                old_normal_firerate : float = player.get_normal_firerate()
                old_special_firerate : float = player.get_special_firerate()
                player.upgrades['AllFirerateMultiplier'] += upgrade_value
                new_normal_firerate : float = player.get_normal_firerate()
                new_special_firerate : float = player.get_special_firerate()
                player.upgrades['AllFirerateMultiplier'] -= upgrade_value
                return f"{old_normal_firerate:.2f}/s --> {new_normal_firerate:.2f}/s\n{old_special_firerate:.2f}/s --> {new_special_firerate:.2f}/s"
            case 'AlternateFireType':
                return ""
            case 'HealHealth':
                old_health = player.current_hp
                new_health = min(player.max_hp, player.current_hp + upgrade_value)
                return f"{old_health} --> {new_health} health"
            case 'HealMax':
                return ""
            case 'MaxHealthBonus':
                return f"{player.max_hp} --> {player.max_hp + upgrade_value} max health"
            case 'RegularDamageBonus':
                old_normal_damage : float = player.get_normal_damage()
                player.upgrades['RegularDamageBonus'] += upgrade_value
                new_normal_damage : float = player.get_normal_damage()
                player.upgrades['RegularDamageBonus'] -= upgrade_value
                return f"{old_normal_damage:.2f} --> {new_normal_damage:.2f} dmg"
            case 'RegularFirerateMultiplier':
                old_normal_firerate : float = player.get_normal_firerate()
                player.upgrades['RegularFirerateMultiplier'] += upgrade_value
                new_normal_firerate : float = player.get_normal_firerate()
                player.upgrades['RegularFirerateMultiplier'] -= upgrade_value
                return f"{old_normal_firerate:.2f}/s --> {new_normal_firerate:.2f}/s"
            case 'SpecialDamageMultipler':
                old_special_damage : float = player.get_special_damage()
                player.upgrades['SpecialDamageMultipler'] += upgrade_value
                new_special_damage : float = player.get_special_damage()
                player.upgrades['SpecialDamageMultipler'] -= upgrade_value
                return f"{old_special_damage:.2f} --> {new_special_damage:.2f} special dmg"
            case 'SpecialFirerateMultiplier':
                old_firerate_damage : float = player.get_special_firerate()
                player.upgrades['SpecialFirerateMultiplier'] += upgrade_value
                new_special_firerate : float = player.get_special_firerate()
                player.upgrades['SpecialFirerateMultiplier'] -= upgrade_value
                return f"{old_firerate_damage:.2f}/s --> {new_special_firerate:.2f}/s"
            case 'DashRechargeRate':
                return f"{Player.DASH_COOLDOWN / player.upgrades['DashRechargeRate']:.2f}s --> {Player.DASH_COOLDOWN / (player.upgrades['DashRechargeRate'] + upgrade_value):.2f}s"
            case _:
                return ""
    @staticmethod
    def format_card_text(upgrade_type : "UpgradeType", upgrade_value : int|float, player : "Player") -> list[tuple[str, int, int|str, ColorType]]:
        DEFAULT_FONT_SIZE : int = 31
        improvement_text : str = ShopControlScript.get_improvement_text(upgrade_type, upgrade_value, player)
        match upgrade_type:
            case 'AllDamageMultiplier':
                normal_improvement, special_improvement = improvement_text.split('\n')
                return [(f"+{upgrade_value:.0%} damage\nto all weapons", 50, DEFAULT_FONT_SIZE, "White"),
                (normal_improvement, 200, DEFAULT_FONT_SIZE, "Light Blue"),
                (special_improvement, 200 + (DEFAULT_FONT_SIZE + 1), DEFAULT_FONT_SIZE, "Purple")]
            case 'AllFirerateMultiplier':
                normal_improvement, special_improvement = improvement_text.split('\n')
                return [(f"+{upgrade_value:.0%} firerate\nwith every weapon", 50, DEFAULT_FONT_SIZE, "White"),
                (normal_improvement, 200, DEFAULT_FONT_SIZE, "Light Blue"),
                (special_improvement, 200 + (DEFAULT_FONT_SIZE + 1), DEFAULT_FONT_SIZE, "Purple")]
            case 'AlternateFireType':
                result = [
                    (f"New special attack:", 50, DEFAULT_FONT_SIZE, "White"), 
                    (src.sprites.player.alternate_fire_base_stats[upgrade_value]['name'], 100, DEFAULT_FONT_SIZE, "White"),
                ]
                for i, line in enumerate(src.sprites.player.alternate_fire_base_stats[upgrade_value]['description'].split('\n')):
                    result.append((line, 150 + (DEFAULT_FONT_SIZE + 1) * i, DEFAULT_FONT_SIZE, "White"))
                return result
            case 'HealHealth':
                return [(f"Heal up to {upgrade_value} health", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Green")]
            case 'HealMax':
                return [(f"Heal up to max HP", 50, DEFAULT_FONT_SIZE, "White")]
            case 'MaxHealthBonus':
                return [(f"Increase max health\nby {upgrade_value}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Green")]
            case 'DashRechargeRate':
                return [(f"Increase dash\nrecharge rate by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Green")]
            case 'RegularDamageBonus':
                return [(f"Increase normal\nprojectile damage by {upgrade_value:.1f}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Light Blue")]
            case 'RegularFirerateMultiplier':
                return [(f"Increase normal\nprojectile firerate by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Light Blue")]
            case 'SpecialDamageMultipler':
                return [(f"Increase special attack\ndamage by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Purple")]
            case 'SpecialFirerateMultiplier':
                return [(f"Increase special attack\nfirerate by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE, "White"),
                        (improvement_text, 200, DEFAULT_FONT_SIZE, "Purple")]
            case 'LazerSpecialist':
                new_level : int = player.upgrades['LazerSpecialist'] + 1
                result = [(f"Lazer specialist {'I' * new_level}:", 50, DEFAULT_FONT_SIZE, "White")]
                match player.upgrades['LazerSpecialist']:
                    case 0:
                        text = f"On hit, the\nlazer splits in\nfour projectiles that\ndeal half damage."
                    case 1:
                        text = f"The lazer now\nsplits one more time\nand conserves 65%\n of the damage\neach split."
                    case 2:
                        text = f"Instead of losing\n35% of the damage,\nthe lazer deals 20%\nmore damage each split."
                for i, line in enumerate(text.split('\n')):
                    result.append((line, 100 + (DEFAULT_FONT_SIZE + 1) * i, DEFAULT_FONT_SIZE, "White"))
                return result
            case 'ShotgunSpecialist':
                new_level : int = player.upgrades['ShotgunSpecialist'] + 1
                result = [(f"Shotgun specialist {'I' * new_level}:", 50, DEFAULT_FONT_SIZE, "White")]
                match player.upgrades['ShotgunSpecialist']:
                    case 0:
                        text = f"On hit, the\nshotgun shells split\nin three, dealing more\ndamage."
                    case 1:
                        text = f"The shotgun shells now\nbounce of the edges\nof the screen twice,\ndealing even more damage."
                    case 2:
                        return [(f"Error:\nShotgun specialist III\ndoes not exist!", 50, DEFAULT_FONT_SIZE, "White")]
                for i, line in enumerate(text.split('\n')):
                    result.append((line, 100 + (DEFAULT_FONT_SIZE + 1) * i, DEFAULT_FONT_SIZE, "White"))
                return result
            case 'RocketSpecialist':
                new_level : int = player.upgrades['RocketSpecialist'] + 1
                result = [(f"Rocket specialist {'I' * new_level}:", 50, DEFAULT_FONT_SIZE, "White")]
                match player.upgrades['RocketSpecialist']:
                    case 0:
                        text = f"The rocket now\nhas an increased\nexplosive range and\ndeals more AOE damage"
                    case 1:
                        return [(f"Error:\nRocket specialist II\ndoes not exist!", 50, DEFAULT_FONT_SIZE, "White")]
                    case 2:
                        return [(f"Error:\nRocket specialist III\ndoes not exist!", 50, DEFAULT_FONT_SIZE, "White")]
                for i, line in enumerate(text.split('\n')):
                    result.append((line, 100 + (DEFAULT_FONT_SIZE + 1) * i, DEFAULT_FONT_SIZE, "White"))
                return result
            case _:
                return [("Unknown upgrade", 50, DEFAULT_FONT_SIZE), (upgrade_type, 100, DEFAULT_FONT_SIZE), (str(upgrade_value), 150, DEFAULT_FONT_SIZE)]

    
    @staticmethod
    def corou(time_source : TimeSource, upgrades : dict["UpgradeType", float|int], player : "Player",
              game_state : ShopGameState) -> Generator[None, float, "UpgradeType"]:
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        delay_timer : Timer = Timer(1.5, time_source)
        x_positions : list[int] = ShopControlScript.generate_x_positions(len(upgrades), centerx)
        cards : list[UpgradeCard] = []
        card_dict : dict[UpgradeType, UpgradeCard] = {}
        for pos, upgrade_type, upgrade_value in zip(x_positions, upgrades.keys(), upgrades.values()):
            card = UpgradeCard.spawn(pos, ShopControlScript.format_card_text(upgrade_type, upgrade_value, player),
                                     special=game_state.major_upgrade)
            cards.append(card)
            card_dict[upgrade_type] = card
        player.can_shoot = False
        yield
        delta : float = core_object.dt
        while not delay_timer.isover():
            new_volume = pygame.math.lerp(1, 0.3, interpolation.quad_ease_out(delay_timer.get_time() / delay_timer.duration))
            ShopControlScript.update_music_volume(new_volume)
            delta = yield
        player.can_shoot = True
        to_remove : list[UpgradeCard] = []
        while True:
            picked_card : UpgradeCard|None = None
            for card in cards:
                if card.check_collisions():
                    picked_card = card
                    break
            if picked_card:
                break
            ShopControlScript.update_music_volume(0.3)
            delta = yield
        for card in cards:
            if card != picked_card:
                card.when_not_picked()
        picked_card.when_picked()
        picked_upgrade_type : UpgradeType = ([k for k in card_dict if card_dict[k] == picked_card])[0]
        game_state.apply_upgrade(picked_upgrade_type)
        music_fadein_timer : Timer = Timer(1.0, time_source)
        if not core_object.bg_manager.get_all_type("Music"):
            core_object.bg_manager.play(MainGameState.main_theme, 1.0)
            ShopControlScript.update_music_volume(0.0)
            start = 0
            interp_style = interpolation.quad_ease_in
        else:
            start = 0.3
            interp_style = interpolation.linear
        while cards:
            to_remove.clear()
            for card in cards:
                if not card.active:
                    to_remove.append(card)
            for card in to_remove:
                cards.remove(card)
            new_volume = pygame.math.lerp(start, 1, interp_style(music_fadein_timer.get_time() / music_fadein_timer.duration))
            ShopControlScript.update_music_volume(new_volume)
            delta = yield
        ShopControlScript.update_music_volume(1.0)
        return picked_upgrade_type

class GameOverGameState(GameState):
    def __init__(self, game_object : "Game", text = "Game over!", prev_state : GameState|None = None):
        self.game : Game = game_object
        self.lost : bool = text == "Game over!"
        self.control_script : GameOverControlScript = GameOverControlScript()
        self.control_script.initialize(self.game.game_timer.get_time, self)
        self.game.alert_player(text)
        core_object.bg_manager.stop_all_music()
        self.prev = prev_state

    def main_logic(self, delta : float):
        Particle.update_all(delta)
        self.control_script.process_frame(delta)
        if self.control_script.is_over:
            pygame.event.post(pygame.Event(core_object.END_GAME, {}))

    def cleanup(self):
        if self.prev: self.prev.cleanup()

class GameOverControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource, state : GameOverGameState):
        return super().initialize(time_source, state)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource, state : GameOverGameState) -> Generator[None, float, str]:
        timer : Timer = Timer(1, time_source)
        delta : float = yield
        if delta is None: delta = core_object.dt
        while not timer.isover():
            delta = yield
        player = Player.active_elements[0]
        if not state.lost:
            return "Done"
        core_object.main_ui.remove(player.ui_alternate_fire_sprite)
        core_object.main_ui.remove(player.ui_dash_sprite)
        timer.set_duration(2)
        core_object.bg_manager.play_sfx(BaseEnemy.enemy_killed_sfx, 1.0)
        ParticleEffect.load_effect('boss_killed').play(player.position, timer.get_time)
        player.kill_instance()
        while not timer.isover():
            delta = yield
        return "Done"


class PausedGameState(GameState):
    def __init__(self, game_object : 'Game', previous : GameState):
        super().__init__(game_object)
        self.previous_state = previous
    
    def unpause(self):
        if not self.game.active: return
        self.game.game_timer.unpause()
        pause_ui1 = core_object.main_ui.get_sprite('pause_overlay')
        pause_ui2 = core_object.main_ui.get_sprite('pause_text')
        if pause_ui1: core_object.main_ui.remove(pause_ui1)
        if pause_ui2: core_object.main_ui.remove(pause_ui2)
        self.game.state = self.previous_state

    def handle_key_event(self, event : pygame.Event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:
                self.unpause()

def runtime_imports():
    global Game
    from framework.game.game_module import Game
    global core_object
    from framework.core.core import core_object

    #runtime imports for game classes
    global src, TestPlayer      
    import src.sprites.test_player
    from src.sprites.test_player import TestPlayer

    global Background
    import src.sprites.background
    from src.sprites.background import Background

    global Player, Upgrades, UpgradeType, AlternateFireTypes, AlternateFireBaseStatLine
    import src.sprites.player
    from src.sprites.player import Player, Upgrades, UpgradeType, AlternateFireTypes, AlternateFireBaseStatLine

    global UpgradeCard
    import src.sprites.upgrade_card
    from src.sprites.upgrade_card import UpgradeCard

    global BaseEnemy, BasicEnemy, EliteEnemy, GunnerEnemy, EnemyTypes, EnemyType, BossTypes, BossType, RunnerEnemy
    import src.sprites.enemy
    from src.sprites.enemy import BaseEnemy, BasicEnemy, EliteEnemy, GunnerEnemy, RunnerEnemy
    from src.sprites.enemy import EnemyTypes, EnemyType, BossTypes, BossType
    src.sprites.enemy.runtime_imports()

    global BasicBoss, BaseBoss, GoldenBoss, SpaceshipBoss, FinalBoss
    import src.sprites.bosses
    from src.sprites.bosses import BasicBoss, BaseBoss, GoldenBoss, SpaceshipBoss, FinalBoss
    src.sprites.bosses.runtime_imports()

    global BaseProjectile
    import src.sprites.projectiles
    from src.sprites.projectiles import BaseProjectile
    src.sprites.projectiles.runtime_imports()

class NetworkTestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False)
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : NetworkTestPattern = NetworkTestPattern()
        self.test_pattern.initialize(self.game.game_timer.get_time)
        host_arg : str = "true" if pygame.key.get_pressed()[pygame.K_f] else "false"
        print("Hosting : " + host_arg.capitalize())
        core_object.log("Hosting : ", host_arg.capitalize())
        peer_id : int = "fsafgasg12345abcsss5"
        network_key : str = "tmp_recv" + peer_id + host_arg
        core_object.networker.set_network_key(network_key)
        core_object.run_js_source_file("networking", {"PEERID" : "fsafgasg12345abcsss5", "IS_HOST" : host_arg,
                                                      "NETWORK_KEY" : core_object.networker.NETWORK_LOCALSTORAGE_KEY})
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.bind(event_type, self.network_event_handler)
        

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()
        for event_type in [core_object.networker.NETWORK_CLOSE_EVENT, core_object.networker.NETWORK_CONNECTION_EVENT, core_object.networker.NETWORK_DISCONNECT_EVENT,
                           core_object.networker.NETWORK_ERROR_EVENT, core_object.networker.NETWORK_RECEIVE_EVENT]:
            core_object.event_manager.unbind(event_type, self.network_event_handler)
        
    
    def network_event_handler(self, event : pygame.Event):
        if event.type == core_object.networker.NETWORK_RECEIVE_EVENT:
            self.game.alert_player(f"Received data {event.data}")
        elif event.type == core_object.networker.NETWORK_ERROR_EVENT:
            self.game.alert_player(f"Network error occured : {event.info}")
        elif event.type == core_object.networker.NETWORK_CLOSE_EVENT:
            self.game.alert_player("Network connection closed")
        elif event.type == core_object.networker.NETWORK_DISCONNECT_EVENT:
            self.game.alert_player("Network disconnected")
        elif event.type == core_object.networker.NETWORK_CONNECTION_EVENT:
            self.game.alert_player("Network connected")

class NetworkTestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    def type_hints(self):
        self.coro_attributes = ['timer', 'cooldown', 'curr_angle']
        self.timer : Timer
        self.cooldown : Timer
        self.curr_angle : float
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50

        new_textsprite : TextSprite = TextSprite((480, 10), "midtop", None, "Waiting...", "Progress",
        text_settings=(textsprite_font, "White", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        core_object.networker.send_network_message("DONE!!!")
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

class TestGameState(NormalGameState):
    def __init__(self, game_object : 'Game'):
        self.game = game_object
        self.player : TestPlayer = TestPlayer.spawn(pygame.Vector2(random.randint(0, 960),random.randint(0, 540)))
        self.particle_effect : ParticleEffect = ParticleEffect.load_effect('test2', persistance=False)
        self.particle_effect.play(pygame.Vector2(480, 270), time_source=self.game.game_timer.get_time)
        src.sprites.test_player.make_connections()
        self.test_pattern : TestPattern = TestPattern()
        self.test_pattern.initialize(self.game.game_timer.get_time)

    def main_logic(self, delta : float):
        super().main_logic(delta)
        self.test_pattern.process_frame()
    
    def cleanup(self):
        src.sprites.test_player.remove_connections()

class TestPattern(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    def type_hints(self):
        self.coro_attributes = ['timer', 'cooldown', 'curr_angle']
        self.timer : Timer
        self.cooldown : Timer
        self.curr_angle : float
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, None, str]:
        textsprite_font : pygame.Font = core_object.menu.font_50

        new_textsprite : TextSprite = TextSprite((480, 10), "midtop", None, "Waiting...", "Progress",
        text_settings=(textsprite_font, "White", False), text_stroke_settings=("Black", 2))
        core_object.main_ui.add(new_textsprite)
        timer : Timer = Timer(0.5, time_source)
        percentage : float = 0
        yield
        while not timer.isover():
            yield
        timer.set_duration(3, restart=True)
        while not timer.isover():
            percentage = pygame.math.lerp(0, 100, timer.get_time() / timer.duration)
            zoom : float = pygame.math.lerp(1, 0.25, interpolation.quad_ease_out(timer.get_time() / timer.duration))
            angle : float = pygame.math.lerp(0, 25, sin(timer.get_time() / timer.duration * 2 * pi * 10), False)
            core_object.game.main_camera.zoom = zoom
            #core_object.game.main_camera.rotation = angle
            new_textsprite.text = f"{percentage:.2f}%"
            yield
        new_textsprite.text = f"{100}% - Done!"
        timer.set_duration(1, restart=True)
        while not timer.isover():
            yield
        core_object.main_ui.remove(new_textsprite)
        return 'Done'

class GameStates:
    NormalGameState = NormalGameState
    TestGameState = TestGameState
    NetworkTestGameState = NetworkTestGameState
    PausedGameState = PausedGameState
    MainGameState = MainGameState
    ShopGameState = ShopGameState


def initialise_game(game_object : 'Game', event : pygame.Event):
    if event.mode == 'test' and (not True):
        game_object.state = game_object.STATES.NetworkTestGameState(game_object)
    else:
        game_object.state = MainGameState(game_object)
