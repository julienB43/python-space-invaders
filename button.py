from dataclasses import dataclass, field
import pygame

from pygame import Color, Surface, Rect
from pygame.font import Font

@dataclass
class Button:
    image_path: str
    pos: tuple[int, int]
    font: Font
    image: Surface = field(init=False)
    rect: Rect = field(init=False)
    base_color: Color
    hovering_color: Color
    text_input: str
    text: Surface = field(init=False)
    text_rect: Rect = field(init=False)
    transform: bool = False
    
    def __post_init__(self):
        self.text = self.font.render(self.text_input, 1, self.base_color)
        self.text_rect = self.text.get_rect(center=self.pos)
        if self.transform:
            self.image = pygame.transform.scale(pygame.image.load(self.image_path), (300, 60))
        else:
            self.image = pygame.image.load(self.image_path)
        self.rect = self.image.get_rect(center=self.pos)
    
    def update(self, window: pygame.Surface):
        if self.image is not None:
            window.blit(self.image, self.rect)
        window.blit(self.text, self.text_rect)

    def check_input(self, position: tuple[int, int]):
        return position[0] in range(self.rect.left, self.rect.right) and position[1] in range(self.rect.top, self.rect.bottom)
    
    def change_color(self, position: tuple[int, int]):
        if self.check_input(position):
            self.text = self.font.render(self.text_input, 1, self.hovering_color)
        else:
            self.font.render(self.text_input, 1, self.base_color)