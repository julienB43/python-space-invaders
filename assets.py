from dataclasses import dataclass, field
from win32api import GetSystemMetrics
import pygame
import os

from pygame import Surface, Mask
from typing import ClassVar
from enum import Enum

WIDTH = GetSystemMetrics(0)
HEIGHT = GetSystemMetrics(1) - 60

LASER_SIZE = (10, 40)

class ShipSize(Enum):
    SMALL = (60, 60)
    MEDIUM = (80, 80)
    LARGE = (100, 100)

class AssetType(Enum):
    LASER = "laser"
    SHIP = "ship"

class ShipSide(Enum):
    PLAYER = "player"
    ENEMY = "enemy"
    
class LaserType(Enum):
    NORMAL = "normal"
    CHARGED = "charged"

class ShipType(Enum):
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"

@dataclass
class Asset:
    x: int
    y: int
    img: Surface | None = None
    mask: Mask = field(init=False)
    
    def draw(self, window: Surface):
        if self.img:
            window.blit(self.img, (self.x, self.y))
    
    def get_width(self) -> int:
        if self.img:
            return self.img.get_width()
        return 0
    
    def get_height(self) -> int:
        if self.img:
            return self.img.get_height()
        return 0

@dataclass
class Laser(Asset):
    
    def __post_init__(self):
        self.mask = pygame.mask.from_surface(self.img)
        
    def move(self, velocity: int):
        self.y += velocity
    
    def off_screen(self, height: int) -> bool:
        return not (self.y <= height and self.y >= 0)
    
    def collision(self, object: Asset) -> bool:
        return collide(object, self)


@dataclass
class Ship(Asset):
    COOLDOWN: ClassVar[int] = 30
    
    health: int = 100
    ship_side: ShipSide = ShipSide.PLAYER
    laser_img: Surface | None = None
    lasers: list[Laser] = field(default_factory=list)
    cooldown_counter: int = 0
    
    def draw(self, window: Surface) -> None:
        super().draw(window)
        for laser in self.lasers:
            laser.draw(window)
        
    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1
    
    def get_shooting_pos(self) -> tuple[int, int]:
        x_pos = self.x + (self.get_width() - self.laser_img.get_width()) // 2
        match self.ship_side:
            case ShipSide.PLAYER:
                y_pos = self.y - self.laser_img.get_height()
            case ShipSide.ENEMY:
                y_pos = self.y + self.laser_img.get_height()
            case _:
                y_pos = 0
        return x_pos, y_pos
        
    def shoot(self):
        if self.cooldown_counter == 0:
            x_pos, y_pos = self.get_shooting_pos()
            laser = Laser(x_pos, y_pos, img=self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1
    
    def move_lasers(self, velocity: int):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(velocity)
    
    def delete_offscreen_laser(self, laser: Laser):
        if laser.off_screen(HEIGHT):
            self.lasers.remove(laser)


@dataclass
class Player(Ship):
    laser_img: Surface
    max_health: int = 100
    
    def __post_init__(self):
        self.ship_side = ShipSide.PLAYER
        self.img = get_image(ShipType.LARGE, self.ship_side, AssetType.SHIP)
        self.laser_img = get_image(LaserType.NORMAL, self.ship_side, AssetType.LASER)
        self.mask = pygame.mask.from_surface(self.img)
    
    def delete_collided_assets(self, laser: Laser, obj: Ship, obj_list: list[Ship]):
        if laser.collision(obj):
            obj_list.remove(obj)
            self.lasers.remove(laser)
    
    def move_lasers(self, velocity: int, obj_list: list[Ship]):
        super().move_lasers(velocity)
        for laser in self.lasers[:]:
            super().delete_offscreen_laser(laser)
            for obj in obj_list[:]:
                self.delete_collided_assets(laser, obj, obj_list)
    
    def healthbar(self, window):
        hbar_width = self.get_width()
        health_ratio = self.health / self.max_health
        hbar_xpos = self.x
        hbar_ypos = self.y + self.get_height() + 10
        pygame.draw.rect(window, "red", (hbar_xpos, hbar_ypos, hbar_width, 5))
        pygame.draw.rect(window, "green", (hbar_xpos, hbar_ypos,hbar_width * health_ratio, 5))
        

@dataclass
class Enemy(Ship):
    ship_type: ShipType = ShipType.SMALL
    laser_type: LaserType = LaserType.NORMAL

    def __post_init__(self):
        self.ship_side = ShipSide.ENEMY
        self.img = get_image(self.ship_type, self.ship_side, AssetType.SHIP)
        self.laser_img = get_image(self.laser_type, self.ship_side, AssetType.LASER)
        self.mask = pygame.mask.from_surface(self.img)
    
    def collision_interaction(self, laser: Laser, obj: Ship):
        self.lasers.remove(laser)
        match self.laser_type:
            case LaserType.NORMAL:
                obj.health -= 10
            case LaserType.CHARGED:
                obj.health -= 20
    
    def move_lasers(self, velocity: int, obj: Laser | Ship):
        super().move_lasers(velocity)
        for laser in self.lasers[:]:
            super().delete_offscreen_laser(laser)
            if laser.collision(obj):
                self.collision_interaction(laser, obj)
    
    def move(self, velocity):
        self.y += velocity


def collide(obj1: Laser | Ship, obj2: Laser | Ship):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None

def get_image_size(asset_type: ShipType | LaserType, obj_type: AssetType) -> tuple[int, int]:
    if obj_type == AssetType.LASER:
        return LASER_SIZE
    match asset_type:
        case ShipType.SMALL:
            return ShipSize.SMALL.value
        case ShipType.MEDIUM:
            return ShipSize.MEDIUM.value
        case ShipType.LARGE:
            return ShipSize.LARGE.value
    return (0, 0)

def get_image(asset_type: ShipType | LaserType, ship_side: ShipSide, obj_type: AssetType):
    file_name = f"{asset_type.value}_{ship_side.value}_{obj_type.value}.png"
    img_size = get_image_size(asset_type, obj_type)
    return pygame.transform.scale(pygame.image.load(os.path.join("assets", file_name)), img_size)