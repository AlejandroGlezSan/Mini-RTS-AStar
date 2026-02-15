from pygame import Vector2
import pygame
from constants import WIDTH, HEIGHT, WORLD_SIZE

class Camera:
    def __init__(self):
        self.offset = Vector2(0, 0)
        self.scroll_speed = 15

    def apply(self, pos):
        return pos + self.offset

    def update(self):
        mouse = pygame.mouse.get_pos()
        if mouse[0] > WIDTH - 25: self.offset.x -= self.scroll_speed
        if mouse[0] < 25: self.offset.x += self.scroll_speed
        if mouse[1] > HEIGHT - 25: self.offset.y -= self.scroll_speed
        if mouse[1] < 25: self.offset.y += self.scroll_speed
        self.offset.x = max(-(WORLD_SIZE - WIDTH), min(0, self.offset.x))
        self.offset.y = max(-(WORLD_SIZE - HEIGHT), min(0, self.offset.y))