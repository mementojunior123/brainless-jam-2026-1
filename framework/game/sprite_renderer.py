import pygame
from collections import deque
from typing import TypeAlias

SpriteCacheLine : TypeAlias = tuple[float, float, pygame.Surface, pygame.Surface] 
# zoom, rotation, original_image, cached_image

class SpriteCamera():
    MAX_SPRITES_CACHED : int = 20
    MAX_CACHE_AMOUNT : int = 5

    def __init__(self):
        self.zoom : float = 1.0
        self.offset : pygame.Vector2 = pygame.Vector2(0, 0)
        self.rotation : float = 0.0
        self._origin : pygame.Vector2|None = None
        self.sprite_cache : dict[Sprite, deque[SpriteCacheLine]] = {}

    @property
    def origin(self) -> pygame.Vector2|None:
        return self._origin
    
    @origin.setter
    def origin(self, new_value : pygame.Vector2|None):
        if self._origin == new_value:
            return
        self._origin = new_value
        self.clear_cache()
    
    def render_sprite(self, sprite : "Sprite", display : pygame.Surface, colorkey = None):
        if self.zoom == 1.0 and self.rotation == 0.0:
            if self.offset.magnitude() == 0.0:
                display.blit(sprite.image, sprite.rect)
            else:
                original_pos : pygame.Vector2 = sprite.position.copy()
                sprite.position -= self.offset
                display.blit(sprite.image, sprite.rect)
                sprite.position = original_pos
            return
        
        transformed : pygame.Surface

        cached : pygame.Surface|None = self._cache_lookup(sprite)
        if cached:
            transformed = cached
        else:
            pivot_compensation_angle : float = 0
            original_image : pygame.Surface = sprite.image
            if sprite.pivot:
                original_image = sprite.pivot.original_image
                pivot_compensation_angle = sprite.pivot.angle
                colorkey = sprite.pivot.img_colorkey
            if colorkey is None:
                colorkey = (0, 255, 0)
            new_image = pygame.transform.rotozoom(original_image.convert_alpha(), self.rotation - pivot_compensation_angle, self.zoom)
            transformed : pygame.Surface = pygame.Surface(new_image.get_size())
            transformed.set_colorkey(colorkey)
            transformed.fill(colorkey)
            transformed.blit(new_image, (0, 0))
            self._add_to_cache(sprite, transformed)
            # TODO : Find a way to not have to create two surfaces each time
        
        origin : pygame.Vector2 = (self.origin or pygame.Vector2(display.get_size()) // 2)
        origin_to_sprite : pygame.Vector2 = pygame.Vector2((sprite.true_position - self.offset) - origin)
        scaled_origin_to_sprite : pygame.Vector2 = origin_to_sprite * self.zoom
        sprite_final_position : pygame.Vector2 = origin + scaled_origin_to_sprite.rotate(-self.rotation)
        transformed_rect : pygame.Surface = transformed.get_rect(center = sprite_final_position)
        display.blit(transformed, transformed_rect)

    def clear_cache(self):
        self.sprite_cache.clear()
    
    def _cache_lookup(self, sprite : "Sprite") -> pygame.Surface|None:
        if sprite not in self.sprite_cache:
            return None
        cache_line : SpriteCacheLine
        for cache_line in self.sprite_cache[sprite]:
            zoom, rotation, original_image, transformed_image = cache_line
            if zoom == self.zoom and rotation == self.rotation and original_image == sprite.image:
                return transformed_image
        return None
    
    def _add_to_cache(self, sprite : "Sprite", transformed_image : pygame.Surface):
        if sprite not in self.sprite_cache:
            self.sprite_cache[sprite] = deque(maxlen=self.MAX_CACHE_AMOUNT)
        self.sprite_cache[sprite].appendleft((self.zoom, self.rotation, sprite.image, transformed_image))
        if len(self.sprite_cache) > self.MAX_SPRITES_CACHED:
            selected : set[Sprite] = set()
            target : int = len(self.sprite_cache) - self.MAX_SPRITES_CACHED
            for sprite in self.sprite_cache:
                selected.add(sprite)
                target -= 1
                if target <= 0:
                    break
            for sprite in selected:
                del self.sprite_cache[sprite]
    



def runtime_imports():
    global Sprite
    from framework.game.sprite import Sprite