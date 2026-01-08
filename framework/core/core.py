import pygame
from time import perf_counter
from collections import deque
from framework.utils.my_timer import Timer
from framework.core.event_manger import EventManger
from framework.networking.networker import Networker
import framework.game.game_module
from framework.game.sprite import Sprite
from src.settings import Settings
from framework.core.bg_manager import BgManager
from framework.core.ui import Ui
from src.menu import Menu
from framework.utils.ui.textsprite import TextSprite
from src.game_storage import GameStorage
import src.menu
from framework.game.game_module import Game
from framework.core.task_scheduler import TaskScheduler
from framework.utils.tween_module import TweenTrack, TweenChain
from framework.utils.animation import AnimationTrack
import sys
import platform
from typing import Any, TypedDict, Callable
from types import SimpleNamespace

class JsSource(TypedDict):
    source : str
    args : dict[str, str|None]
    allow_default : bool

WEBPLATFORM = 'emscripten'

class Core:
    CORE_EVENT = pygame.event.custom_type()
    START_GAME = pygame.event.custom_type()
    END_GAME = pygame.event.custom_type()

    IS_DEBUG : bool = False
    def __init__(self) -> None:
        self.FPS = 60
        self.PERFORMANCE_MODE = False
        self.WEBPLATFORM = 'emscripten'
        self.CURRENT_PLATFORM = sys.platform
        self.MIX_UI_AND_SPRITES : bool = False
        self.main_display : pygame.Surface
        self.brightness_map = pygame.Surface((2000, 2000), pygame.SRCALPHA)
        pygame.draw.rect(self.brightness_map, (255, 255, 255, 0), (0,0, 2000, 2000))
        self.event_manager = EventManger()
        self.make_connections()

        self.active_fingers : dict[int, tuple[float, float]] = {}
        self.dt : float = 1
        self.last_dt_measurment : float = 0

        self.settings = Settings()
        self.bg_manager = BgManager()
        self.main_ui = Ui()
        self.menu = Menu()
        self.game = Game()
        self.storage = GameStorage()
        self.task_scheduler = TaskScheduler()
        self.delta_stream : deque[float] = deque([1 for _ in range(30)])
        self.dirty_display_rects : list[pygame.Rect] = []
        self.brightness_map_blend_mode = pygame.BLENDMODE_NONE

        self.global_timer : Timer = Timer(-1, perf_counter, 1)
        Timer.time_source = self.global_timer.get_time

        self.window_bools : dict = {'Shown' : True, 'input_focused' : True}
        self.frame_counter : int = 0
        self.show_fps_timer : Timer = Timer(0.1, self.global_timer.get_time)
        self.fps_sprite : TextSprite = TextSprite(pygame.Vector2(15 + 63 - 63, 10), 'topleft', 0, 'FPS : 0', 'fps_sprite', 
                            text_settings=(Menu.font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0))
        self.fps_sprite.visible = False
        self.debug_sprite : TextSprite = TextSprite(pygame.Vector2(15, 200), 'midright', 0, '', 'debug_sprite', 
                            text_settings=(Menu.font_40, 'White', False), text_stroke_settings=('Black', 2),
                            text_alingment=(9999, 5), colorkey=(255, 0,0), zindex=999)
        self.event_manager.bind(self.START_GAME, self.start_game)
        self.event_manager.bind(self.END_GAME, self.end_game)
        self.js_source : dict[str, JsSource] = {}
        self.networker : Networker = Networker(self)
    
    def load_js_source_file(self, file_path : str, script_name : str, args : dict[str, str|None]|None = None, allow_default : bool = True) -> bool:
        if args is None: args = {}
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                source_dict : JsSource = {}
                source_dict['source'] = file.read()
                source_dict['allow_default'] = allow_default
                source_dict['args'] = args
                self.js_source[script_name] = source_dict
        except FileNotFoundError:
            return False
        return True
    
    def run_js_source_file(self, script_name : str, args : dict[str, str]|None = None) -> bool:
        if not self.is_web():
            print("Cannot run js file in a non-web context!")
            return False
        if args is None: args = {}
        if script_name not in self.js_source:
            return False
        script : JsSource = self.js_source[script_name]
        current_source : str = script['source']
        used_args : dict[str, str] = script['args'].copy()
        if not script['allow_default']:
            for arg_name in used_args:
                if arg_name not in args:
                    return False
        for arg_name in args:
            if arg_name in used_args:
                used_args[arg_name] = args[arg_name]
        for arg_name in used_args:
            if used_args[arg_name] is None:
                return False
        for arg_name in used_args:
            current_source = current_source.replace(f"`{{{arg_name}}}`", used_args[arg_name])

        self.run_js_code(current_source)
        return True
    
    def start_game(self, event : pygame.Event):
        if event.type != self.START_GAME: return
        
        self.menu.prepare_exit()
        self.game.start_game(event)

        self.event_manager.bind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
        self.event_manager.bind(pygame.FINGERDOWN, Sprite.handle_touch_event)
        self.event_manager.bind(pygame.KEYDOWN, self.detect_game_over)

        
        self.main_ui.add(self.fps_sprite)
        self.main_ui.add(self.debug_sprite)
    
    def detect_game_over(self, event : pygame.Event):
        pass
    
    def end_game(self, event : pygame.Event = None):
        self.game.end_game()
        self.menu.prepare_entry(1)
        self.event_manager.unbind(pygame.MOUSEBUTTONDOWN, Sprite.handle_mouse_event)
        self.event_manager.unbind(pygame.FINGERDOWN, Sprite.handle_touch_event)
        self.event_manager.unbind(pygame.KEYDOWN, self.detect_game_over)

    def is_web(self) -> bool:
        return self.CURRENT_PLATFORM == WEBPLATFORM
    
    def setup_web(self, method : int = 2):
        if not self.is_web(): return
        if method == 1:
            platform.window.onfocus = self.continue_things
            platform.window.onblur = self.stop_things
        elif method == 2:
            platform.EventTarget.addEventListener(platform.window, "blur", self.stop_things)
            platform.EventTarget.addEventListener(platform.window, "focus", self.continue_things)
            platform.EventTarget.addEventListener(platform.window, "beforeunload", self.save_game)
        self.storage.set_web(self.networker.NETWORK_LOCALSTORAGE_KEY, "")
    
    def save_game(self):
        self.storage.save(self.is_web())
        self.settings.save(self.is_web())


    def init(self, main_display : pygame.Surface):
        self.main_display = main_display
    
    def close_game(self, event : pygame.Event):
        self.save_game()
        pygame.quit()
        exit()
    
    def update_dt(self, target_fps : int|float = 60):
        if self.last_dt_measurment == 0:
            self.dt = 1
            self.last_dt_measurment = perf_counter()
        else:
            mark = perf_counter()
            self.dt = (mark - self.last_dt_measurment) * target_fps
            self.last_dt_measurment = mark
    
    def set_debug_message(self, text : str):
        debug_textsprite : TextSprite = self.main_ui.get_sprite('debug_sprite')
        if not debug_textsprite: return
        debug_textsprite.text = text
    
    def set_brightness(self, new_val : int):
        brightness = new_val
        abs_brightness = abs(new_val)
        if brightness >= 0:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_ADD
        else:
            pygame.draw.rect(self.brightness_map, (abs_brightness, abs_brightness, abs_brightness), (0,0, 2000, 2000))
            self.brightness_map_blend_mode = pygame.BLEND_RGB_SUB
    
    def make_connections(self):
        self.event_manager.bound_actions[pygame.QUIT] = [self.close_game]

        self.event_manager.bind(pygame.WINDOWHIDDEN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWSHOWN, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSGAINED, self.handle_window_event)
        self.event_manager.bind(pygame.WINDOWFOCUSLOST, self.handle_window_event)

        self.event_manager.bind(pygame.FINGERDOWN, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERMOTION, self.process_touch_event)
        self.event_manager.bind(pygame.FINGERUP, self.process_touch_event)
    
    def process_touch_event(self, event : pygame.Event):
        if event.type == pygame.FINGERDOWN:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.FINGERUP:
            self.active_fingers.pop(event.finger_id, None)
        
        elif event.type == pygame.FINGERMOTION:
            x = event.x * self.main_display.get_width()
            y = event.y * self.main_display.get_height()
            self.active_fingers[event.finger_id] = (x,y)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.active_fingers[10] = (event.pos)
        
        elif event.type == pygame.MOUSEMOTION:
            self.active_fingers[10] = (event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            self.active_fingers.pop(10, None)
    
    def process_core_event(self, event : pygame.Event):
        pass

    def handle_window_event(self, event : pygame.Event):
        platform : str = sys.platform[0:]
        if platform != 'emscripten': return
        return
        if event.type == pygame.WINDOWFOCUSLOST:
            self.window_bools['input_focused'] = False
            self.set_debug_message('Window Unfocused')
            self.stop_things()

        elif event.type == pygame.WINDOWHIDDEN:
            self.window_bools['Shown'] = False
            self.set_debug_message('Window Hidden')
            self.global_timer.pause()
            self.game.pause()

        elif event.type == pygame.WINDOWSHOWN:
            self.window_bools['Shown'] = True
            return
            self.set_debug_message('Window Shown')
            self.global_timer.unpause()
        
        elif event.type == pygame.WINDOWFOCUSGAINED:
            self.window_bools['input_focused'] = True
            self.set_debug_message('Window Focused')
            self.continue_things()

    def check_window_focus(self):
        platform : str = sys.platform[0:]
        if platform != 'emscripten': return True
        result = pygame.display.get_active()
        self.set_debug_message('Window Focused') if result else self.set_debug_message('Window Unfocused')
        return pygame.key.get_focused()
    
    def stop_things(self, event : Any|None = None):
        self.global_timer.pause()
        self.game.pause()
        if event is not None: self.window_bools['input_focused'] = False 
    
    def continue_things(self, event : Any|None = None):
        self.global_timer.unpause() 
        if event is not None: self.window_bools['input_focused'] = True 


    def update(self):
        self.task_scheduler.update()
        TweenTrack.update_all()
        TweenChain.update_all()
        self.update_delta_stream()
        self.bg_manager.update()
        AnimationTrack.update_all_elements()
        if self.show_fps_timer.isover():
            self.update_fps_sprite()
            self.show_fps_timer.restart()
        if self.is_web():
            self.networker.update()
    
    def update_delta_stream(self):
        target_lentgh = round(30 / self.dt)
        current_lentgh = len(self.delta_stream)
        if current_lentgh == target_lentgh:
            self.delta_stream.popleft()
        elif current_lentgh > target_lentgh:
            self.delta_stream.popleft()
            self.delta_stream.popleft()
        self.delta_stream.append(self.dt)
    
    def get_fps(self):
        total = 0
        for delta in self.delta_stream:
            total += delta
        
        average = total / len(self.delta_stream)
        return 60 / average

    def update_fps_sprite(self):
        if self.fps_sprite.visible:
            self.fps_sprite.text = f'FPS : {self.get_fps():0.0f}'
    
    def run_js_code(self, code : str) -> Any:
        if not self.is_web():
            print("Warning : Shouldn't use Core.run_js_code in a non web context")
            return None
        return platform.eval(code)
    
    def log(self, *args : list[Any], sep=' '):
        print(sep.join(str(arg) for arg in args))
        if self.is_web():
            self.log_to_js_console(sep.join(args))
    
    def log_to_js_console(self, info : str):
        if not self.is_web():
            print("Warning : Shouldn't use Core.log_to_js_console in a non web context")
            return
        lines = info.split("\n")
        code = ''.join([f"console.log(String.raw`{line.replace("`", "'")}`);" for line in lines])
        platform.eval(code)
    
    def alert_js(self, info : str):
        if not self.is_web():
            print("Warning : Shouldn't use Core.log_to_js_console in a non web context")
            return
        lines = info.split("\n")
        code = ''.join([f"alert(String.raw`{line.replace("`", "'")}`);" for line in lines])
        platform.eval(code)
    
    def get_platform_attribute(self, attr : str, default : Any = None) -> Any:
        if not self.is_web():
            print("Warning : Shouldn't use Core.get_platform_attribute in a non web context")
            return default
        return getattr(platform, attr, default)

    def dump_platform_vars(self) -> None|dict[str, Any]:
        if not self.is_web():
            print("Warning : Shouldn't use Core.dump_platform_vars in a non web context")
            return None
        return platform.__dict__
    
    def __hints(self):
        global TextSprite
        from framework.utils.ui.textsprite import TextSprite

core_object = Core()
setattr(src.menu, 'core_object', core_object)