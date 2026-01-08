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
from framework.utils.helpers import average, random_float
from framework.utils.ui.brightness_overlay import BrightnessOverlay
from framework.utils.particle_effects import ParticleEffect

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
    enemies : dict["EnemyType", int]
    spawn_cooldown : float
    spawn_rate_penalty_per_enemy : float
    bosses : list["BossType"]

WAVE_DATA : dict[int, WaveData] = {
    1 : {
        'enemies' : {
            'basic' : 5,
        },
        "spawn_cooldown" : 2.9,
        "spawn_rate_penalty_per_enemy" : 1.0,
        'bosses' : []
    },

    2 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 1,
            'gunner' : 1,
        },
        "spawn_cooldown" : 2.7,
        "spawn_rate_penalty_per_enemy" : 1,
        'bosses' : []
    },

    3 : {
        'enemies' : {
            'basic' : 5,
            'elite' : 3,
            'gunner' : 2,
        },
        "spawn_cooldown" : 2.4,
        "spawn_rate_penalty_per_enemy" : 0.5,
        'bosses' : []
    },

    4 : {
        'enemies' : {
            'basic' : 6,
            'elite' : 5,
            'gunner' : 3
        },
        "spawn_cooldown" : 2.1,
        "spawn_rate_penalty_per_enemy" : 0.2,
        'bosses' : []
    },

    5 : {
        'enemies' : {
            'basic' : 6,
            'elite' : 6,
            'gunner' : 4
        },
        "spawn_cooldown" : 2.0,
        "spawn_rate_penalty_per_enemy" : 0.2,
        'bosses' : ['basic_boss']
    },

    6 : {
        'enemies' : {
            'basic' : 7,
            'elite' : 6,
            'gunner' : 5
        },
        "spawn_cooldown" : 1.25,
        "spawn_rate_penalty_per_enemy" : 0.25,
        'bosses' : []
    },

    7 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 8,
            'gunner' : 6
        },
        "spawn_cooldown" : 1.20,
        "spawn_rate_penalty_per_enemy" : 0.2,
        'bosses' : []
    },

    8 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 8,
            'gunner' : 6
        },
        "spawn_cooldown" : 1.0,
        "spawn_rate_penalty_per_enemy" : 0.2,
        'bosses' : []
    },

    9 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 10,
            'gunner' : 6
        },
        "spawn_cooldown" : 1.0,
        "spawn_rate_penalty_per_enemy" : 0.15,
        'bosses' : []
    },

    10 : {
        'enemies' : {
            'basic' : 4,
            'elite' : 10,
            'gunner' : 6
        },
        "spawn_cooldown" : 0.9,
        "spawn_rate_penalty_per_enemy" : 0.15,
        'bosses' : ['basic_boss']
    },
}

class MainGameState(NormalGameState):
    main_theme : pygame.Sound = pygame.Sound("assets/audio/music/theme2_trimmed.ogg")
    main_theme.set_volume(0.3)

    boss_theme : pygame.Sound = pygame.Sound("assets/audio/music/theme1.ogg")
    boss_theme.set_volume(0.2)

    def __init__(self, game_object : "Game", prev_main_state : Union["MainGameState", None] = None, wave_num : int = 1):
        self.game : Game = game_object
        self.player : Player
        self.screen_size : tuple[int, int]
        if prev_main_state is None:
            self.spawn_background()
            self.player = Player.spawn("midbottom", pygame.Vector2(480, 520))
            self.screen_size = core_object.main_display.get_size()
            core_object.bg_manager.play(self.main_theme, 1.0)
            ShopControlScript.update_music_volume(1.0)
            src.sprites.player.make_connections()
        else:
            self.player = prev_main_state.player
            self.screen_size = prev_main_state.screen_size
        
        self.control_script : BasicWaveControlScript = BasicWaveControlScript()
        self.control_script.initialize(self.game.game_timer.get_time, wave_num)

        self.wave_number : int = wave_num
        self.game.alert_player(f"Wave {self.wave_number} start")
        if not core_object.bg_manager.get_all_type("Music"):
            core_object.bg_manager.play(self.main_theme, 1.0, fade_ms=2000)
    def spawn_background(self):
        bg = Background.spawn(0)
        while True:
            if bg.rect.bottom < core_object.main_display.get_size()[1]:
                bg = Background.spawn(bg.rect.bottom)
            else:
                break

    def main_logic(self, delta : float):
        Sprite.update_all_sprites(delta)
        Sprite.update_all_registered_classes(delta)
        self.control_script.process_frame(delta)
        if self.player.current_hp <= 0:
            self.transition_to_gameover()
        if self.control_script.is_over:
            self.transition_to_shop()
        

    def transition_to_gameover(self):
        self.game.state = GameOverGameState(self.game)
    
    def transition_to_shop(self):
        self.game.state = ShopGameState(self.game, self.wave_number, self)
    

    def cleanup(self):
        super().cleanup()
        src.sprites.player.remove_connections()
        core_object.bg_manager.stop_all_music()


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
    def spawn_enemy(enemy_type : "EnemyType", x_level : int):
        if enemy_type == EnemyTypes.BASIC.value:
            BasicEnemy.spawn("midtop", pygame.Vector2(x_level, 20))
        elif enemy_type == EnemyTypes.ELITE.value:
            EliteEnemy.spawn("midtop", pygame.Vector2(x_level, 20))
        elif enemy_type == EnemyTypes.GUNNER.value:
            GunnerEnemy.spawn("midtop", pygame.Vector2(x_level, 20))
        else:
            core_object.log(f"Enemy type '{enemy_type}' not found!")
    
    @staticmethod
    def spawn_boss(boss_type : "BossType") -> "BaseBoss":
        core_object.game.alert_player("Boss incoming!")
        if boss_type == "basic_boss":
            return BasicBoss.spawn()
        else:
            core_object.log(f"Enemy type '{boss_type}' not found")
    
    @staticmethod
    def corou(time_source : TimeSource, wave_number : int) -> Generator[None, float, str]:
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        wave_data : WaveData = WAVE_DATA[wave_number]
        enemies : dict[EnemyType, int] = wave_data["enemies"].copy()
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
                enemy_type_chosen : EnemyType = BasicWaveControlScript.pick_random_enemy(enemies)
                enemies[enemy_type_chosen] -= 1
                BasicWaveControlScript.spawn_enemy(enemy_type_chosen, random.randint(100, screen_sizex - 100))
            if pygame.key.get_pressed()[pygame.K_p]:
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
        return "Done"

class ShopGameState(NormalGameState):
    def __init__(self, game_object : "Game", finished_wave : int, prev : "MainGameState"):
        self.game : "Game" = game_object
        self.prev : MainGameState = prev
        self.finished_wave : int = finished_wave
        self.control_script : ShopControlScript = ShopControlScript()
        self.candidates : dict["UpgradeType", float|int] = self.pick_candidates()
        self.control_script.initialize(self.game.game_timer.get_time, self.candidates, self.prev.player, self)
        self.game.alert_player("Shop entered!")

    def pick_candidates(self, count : int = 3) -> dict["UpgradeType", float|int]:
        candidates : dict[UpgradeType, float|int]
        if self.finished_wave % 5 != 0:
            candidates = {
                'RegularDamageBonus' : 0.4,
                'SpecialDamageMultipler' : 0.3,
                'AllDamageMultiplier' : 0.15,

                'RegularFirerateMultiplier' : 0.2,
                'SpecialFirerateMultiplier' : 0.2,
                'AllFirerateMultiplier' : 0.1,

                'MaxHealthBonus' : 1,
                'HealHealth' : 2,
            }
        else:
            candidates = {
                'AllDamageMultiplier' : 0.5,
                'AllFirerateMultiplier' : 0.5,
                'AlternateFireType' : random.choice([AlternateFireTypes.SHOTGUN.value])
            }
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
        super().cleanup()
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
    def get_improvement_text(upgrade_type : "UpgradeType", upgrade_value : int|float) -> str:
        return ""
    
    @staticmethod
    def format_card_text(upgrade_type : "UpgradeType", upgrade_value : int|float) -> list[tuple[str, int, int|str]]:
        DEFAULT_FONT_SIZE : int = 28
        match upgrade_type:
            case 'AllDamageMultiplier':
                return [(f"+{upgrade_value:.0%} damage\nto all weapons", 50, DEFAULT_FONT_SIZE)]
            case 'AllFirerateMultiplier':
                return [(f"+{upgrade_value:.0%} firerate\nwith every weapon", 50, DEFAULT_FONT_SIZE)]
            case 'AlternateFireType':
                return [
                    (f"New special attack:", 50, DEFAULT_FONT_SIZE), 
                    (src.sprites.player.alternate_fire_base_stats[upgrade_value]['name'], 100, DEFAULT_FONT_SIZE),
                    (src.sprites.player.alternate_fire_base_stats[upgrade_value]['description'], 150, DEFAULT_FONT_SIZE)
                ]
            case 'HealHealth':
                return [(f"Heal up to {upgrade_value} health", 50, DEFAULT_FONT_SIZE)]
            case 'HealMax':
                return [(f"Heal up to max HP", 50, DEFAULT_FONT_SIZE)]
            case 'MaxHealthBonus':
                return [(f"Increase max health\nby {upgrade_value}", 50, DEFAULT_FONT_SIZE)] 
            case 'RegularDamageBonus':
                return [(f"Increase normal\nprojectile damage by {upgrade_value:.1f}", 50, DEFAULT_FONT_SIZE)]
            case 'RegularFirerateMultiplier':
                return [(f"Increase normal\nprojectile firerate by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE)]
            case 'SpecialDamageMultipler':
                return [(f"Increase special attack\ndamage by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE)]
            case 'SpecialFirerateMultiplier':
                return [(f"Increase special attack\nfirerate by {upgrade_value:.0%}", 50, DEFAULT_FONT_SIZE)]

            case _:
                return [("Unknown upgrade", 50, DEFAULT_FONT_SIZE), (upgrade_type, 100, DEFAULT_FONT_SIZE), (str(upgrade_value), 150, DEFAULT_FONT_SIZE)]

    
    @staticmethod
    def corou(time_source : TimeSource, upgrades : dict["UpgradeType", float|int], player : "Player",
              game_state : ShopGameState) -> Generator[None, float, "UpgradeType"]:
        screen_size = core_object.main_display.get_size()
        screen_sizex, screen_sizey = screen_size
        centerx, centery = screen_sizex // 2, screen_sizey // 2

        delay_timer : Timer = Timer(2, time_source)
        x_positions : list[int] = ShopControlScript.generate_x_positions(len(upgrades), centerx)
        cards : list[UpgradeCard] = []
        card_dict : dict[UpgradeType, UpgradeCard] = {}
        for pos, upgrade_type, upgrade_value in zip(x_positions, upgrades.keys(), upgrades.values()):
            card = UpgradeCard.spawn(pos, ShopControlScript.format_card_text(upgrade_type, upgrade_value))
            cards.append(card)
            card_dict[upgrade_type] = card
        player.can_shoot = False
        yield
        delta : float = core_object.dt
        while not delay_timer.isover():
            new_volume = pygame.math.lerp(1, 0.2, interpolation.quad_ease_out(delay_timer.get_time() / delay_timer.duration))
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
            ShopControlScript.update_music_volume(0.2)
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
            ShopControlScript.update_music_volume(0.2)
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
    def __init__(self, game_object : "Game"):
        self.game : Game = game_object
        self.control_script : GameOverControlScript = GameOverControlScript()
        self.control_script.initialize(self.game.game_timer.get_time)
        self.game.alert_player("Game over!")
        core_object.bg_manager.stop_all_music()
    
    def main_logic(self, delta : float):
        self.control_script.process_frame(delta)
        if self.control_script.is_over:
            pygame.event.post(pygame.Event(core_object.END_GAME, {}))

    def cleanup(self):
        pass

class GameOverControlScript(CoroutineScript):
    def initialize(self, time_source : TimeSource):
        return super().initialize(time_source)
    
    def type_hints(self):
        self.coro_attributes = []
    
    def process_frame(self, values : float) -> None|str:
        return super().process_frame(values)
    
    @staticmethod
    def corou(time_source : TimeSource) -> Generator[None, float, str]:
        timer : Timer = Timer(1, time_source)
        delta : float = yield
        if delta is None: delta = core_object.dt
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

    global BaseEnemy, BasicEnemy, EliteEnemy, GunnerEnemy, EnemyTypes, EnemyType, BossTypes, BossType
    import src.sprites.enemy
    from src.sprites.enemy import BaseEnemy, BasicEnemy, EliteEnemy, GunnerEnemy, EnemyTypes, EnemyType, BossTypes, BossType
    src.sprites.enemy.runtime_imports()

    global BasicBoss, BaseBoss
    import src.sprites.bosses
    from src.sprites.bosses import BasicBoss, BaseBoss
    src.sprites.bosses.runtime_imports()

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
