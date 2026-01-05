import pygame
from framework.game.sprite import Sprite
from framework.core.core import core_object

from framework.utils.animation import Animation
from framework.utils.pivot_2d import Pivot2D


class TestPlayer(Sprite):
    debug_circle_size : int = 10
    debug_circle = pygame.Surface((debug_circle_size, debug_circle_size))
    debug_circle.set_colorkey((0, 255, 0))
    debug_circle.fill((0,255 ,0))
    pygame.draw.circle(debug_circle, 'Red', (debug_circle_size // 2, debug_circle_size // 2), debug_circle_size // 2)
    IMAGE_SIZE : tuple[int, int]|list[int] = (20, 60)
    test_anim : Animation = Animation.get_animation("test")
    active_elements : list['TestPlayer'] = []
    inactive_elements : list['TestPlayer'] = []
    linked_classes : list['Sprite'] = [Sprite]
    #load assets
    test_image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
    pygame.draw.rect(test_image, "Red", (0,0, *IMAGE_SIZE))

    colors : list[str] = ["Red", "Green", "Blue", "Yellow", "Orange", "Purple", "Black", "White"]
    surface_list : list[pygame.Surface] = []
    surfaces : dict[str, pygame.Surface] = {}
    for color in colors:
        image : pygame.Surface = pygame.surface.Surface(IMAGE_SIZE)
        pygame.draw.rect(image, color, (0,0, *IMAGE_SIZE))
        surfaces[color] = image
        surface_list.append(image)

    def __init__(self) -> None:
        super().__init__()
        self.color_images : dict[str, pygame.Surface]
        self.color_image_list : list[pygame.Surface]
        self.last_mouse_pos : tuple[int, int]
        TestPlayer.inactive_elements.append(self)

    @classmethod
    def spawn(cls, new_pos : pygame.Vector2):
        element = cls.inactive_elements[0]

        element.image = cls.test_image
        element.color_images = cls.surfaces
        element.color_image_list = cls.surface_list
        element.rect = element.image.get_rect()

        element.position = new_pos
        element.align_rect()
        element.zindex = 0

        element.pivot = Pivot2D(element._position, element.image, (0, 255, 0))
        element.pivot.pivot_offset = pygame.Vector2(-0, 30)
        element.last_mouse_pos = pygame.mouse.get_pos()
        track = cls.test_anim.load(element, core_object.game.game_timer.get_time)
        track.play()
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element
    
    def update(self, delta: float):
        keyboard_map = pygame.key.get_pressed()
        move_vector : pygame.Vector2 = pygame.Vector2(0,0)
        speed : int = 5
        if keyboard_map[pygame.K_a]:
            move_vector += pygame.Vector2(-1, 0)
        if keyboard_map[pygame.K_d]:
            move_vector += pygame.Vector2(1, 0)
        if keyboard_map[pygame.K_s]:
            move_vector += pygame.Vector2(0, 1)
        if keyboard_map[pygame.K_w]:
            move_vector += pygame.Vector2(0, -1)
        if keyboard_map[pygame.K_e]:
            self.angle += 5 * delta
        if keyboard_map[pygame.K_q]:
            self.angle -= 5 * delta
        if move_vector.magnitude(): move_vector.normalize()
        self.position += move_vector * speed * delta
        self.clamp_rect(pygame.Rect(0,0, *core_object.main_display.get_size()))
    
    def clean_instance(self):
        self.image = None
        self.color_images = None
        self.color_image_list = None
        self.rect = None
        self.pivot = None
        self._position = pygame.Vector2(0,0)
        self.zindex = None
    
    def draw(self, display : pygame.Surface):
        super().draw(display)
        display.blit(self.debug_circle, pygame.mouse.get_pos())
    
    def handle_mouse_event(self, event : pygame.Event):
        if event.type == pygame.MOUSEMOTION:
            self.last_mouse_pos = event.pos
    
    @classmethod
    def receive_event(cls, event : pygame.Event):
        for element in cls.active_elements:
            if event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                element.handle_mouse_event(event)
        

TestPlayer()
Sprite.register_class(TestPlayer)

def make_connections():
    core_object.event_manager.bind(pygame.MOUSEBUTTONDOWN, TestPlayer.receive_event)
    core_object.event_manager.bind(pygame.MOUSEBUTTONUP, TestPlayer.receive_event)
    core_object.event_manager.bind(pygame.MOUSEMOTION, TestPlayer.receive_event)

def remove_connections():
    core_object.event_manager.unbind(pygame.MOUSEBUTTONDOWN, TestPlayer.receive_event)
    core_object.event_manager.unbind(pygame.MOUSEBUTTONUP, TestPlayer.receive_event)
    core_object.event_manager.unbind(pygame.MOUSEMOTION, TestPlayer.receive_event)