import pygame
from framework.game.sprite import Sprite
from framework.utils.helpers import load_alpha_to_colorkey
from framework.core.core import core_object

class Background(Sprite):
    active_elements : list['Background'] = []
    inactive_elements : list['Background'] = []
    linked_classes : list['Sprite'] = [Sprite]

    default_image : pygame.Surface = load_alpha_to_colorkey("assets/graphics/background/my_background-wide.png", (0, 255, 0))
    BACKGROUND_SPEED : float = 2
    SPAWN_BACKGROUND : bool = True
    display_size : tuple[int, int] = core_object.main_display.get_size()
    def __init__(self) -> None:
        super().__init__()
        Background.inactive_elements.append(self)

    @classmethod
    def spawn(cls, bottom : int):
        element = cls.inactive_elements[0]

        element.image = cls.default_image
        element.rect = element.image.get_rect()

        element.position = pygame.Vector2(0, 0)
        element.move_rect("midbottom", pygame.Vector2(Background.display_size[0] // 2, bottom))
        element.zindex = -1000
        element.current_camera = core_object.game.main_camera
        cls.unpool(element)
        return element

    def update(self, delta: float):
        print(self.rect)
    
    @classmethod
    def update_class(cls, delta : float):
        if not cls.active_elements:
            return
        cls.active_elements.sort(key = lambda b : b.rect.top, reverse=True)
        i : int = 0
        while i < len(cls.active_elements):
            frontrunner : Background = cls.active_elements[i]
            frontrunner.position += pygame.Vector2(0, cls.BACKGROUND_SPEED) * delta
            frontrunner.align_rect()
            if frontrunner.rect.top >= Background.display_size[1]:
                frontrunner.kill_instance()
            else:
                break
        for i, element in enumerate(cls.active_elements):
            if i == 0:
                continue
            prev_background : Background = cls.active_elements[i - 1]
            if prev_background.rect.top >= Background.display_size[1] or prev_background.rect.top < 0:
                continue
            element.move_rect("bottom", prev_background.rect.top)
        highest_background : int = min([element.rect.top for element in cls.active_elements if not element._zombie])
        if highest_background > 0 and cls.SPAWN_BACKGROUND:
            cls.spawn(highest_background)
    
    def clean_instance(self):
        self.image = None
        self.rect = None
        self._position = pygame.Vector2(0,0)
        self.zindex = None
        

for _ in range(5): Background()
Sprite.register_class(Background)
