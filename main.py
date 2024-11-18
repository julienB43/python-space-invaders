import pygame
import random
import os
import time
from dataclasses import dataclass, field
from typing import ClassVar

# Init the font of the pygame window
pygame.font.init()

# Init the pygame window
WIDTH = 720
HEIGHT = 720
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invader game")

# Load images
EASY_ENEMY_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_ship_1.png")), (60, 60))
MEDIUM_ENEMY_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_ship_2.png")), (80, 80))
HARD_ENEMY_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_ship_3.png")), (100, 100))
SMALL_ENEMY_BEAM = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_beam_2.png")), (10, 40))
BIG_ENEMY_BEAM = pygame.transform.scale(pygame.image.load(os.path.join("assets", "enemy_beam_1.png")), (10, 40))
PLAYER_SHIP = pygame.transform.scale(pygame.image.load(os.path.join("assets", "player_ship.png")), (100, 100))
PLAYER_SHIP_BEAM = pygame.transform.scale(pygame.image.load(os.path.join("assets", "player_ship_beam.png")), (10, 40))
SPACE_BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("assets", "space_background.png")), (WIDTH, HEIGHT))


@dataclass
class GameObj:
    x: int
    y: int
    mask: pygame.Mask
    health: int = 100

@dataclass
class Laser(GameObj):
    img: pygame.Surface = SMALL_ENEMY_BEAM
    mask: pygame.Mask = pygame.mask.from_surface(img)
    
    def draw(self, window: pygame.Surface):
        window.blit(self.img, (self.x, self.y))
        
    def move(self, velocity):
        self.y += velocity
    
    def off_screen(self, height):
        return not (self.y <= height and self.y >= 0)
    
    def collision(self, object):
        return collide(object, self)


@dataclass
class Ship(GameObj):
    COOLDOWN = 30
    
    health: int = 100
    ship_type: str = "enemy"
    ship_img: pygame.Surface | None = None
    laser_img: pygame.Surface | None = None
    lasers: list[Laser] = field(default_factory=list)
    cooldown_counter: int = 0
    
    def draw(self, window: pygame.Surface) -> None:
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)
    
    def move_lasers(self, velocity: int, obj: GameObj):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                self.lasers.remove(laser)
                obj.health -= 10
        
    def cooldown(self):
        if self.cooldown_counter >= self.COOLDOWN:
            self.cooldown_counter = 0
        elif self.cooldown_counter > 0:
            self.cooldown_counter += 1
        
    def shoot(self):
        if self.cooldown_counter == 0:
            x_pos = self.x + (self.ship_img.get_width() - self.laser_img.get_width()) / 2
            match self.ship_type:
                case "player":
                    y_pos = self.y - self.laser_img.get_height()
                case "enemy":
                    y_pos = self.y + self.laser_img.get_height()
            laser = Laser(x_pos, y_pos, img=self.laser_img)
            self.lasers.append(laser)
            self.cooldown_counter = 1
    
    def get_width(self) -> int:
        return self.ship_img.get_width()
    
    def get_height(self) -> int:
        return self.ship_img.get_height()


@dataclass
class Player(Ship):
    ship_type: str = "player"
    ship_img: pygame.Surface = PLAYER_SHIP
    laser_img: pygame.Surface = PLAYER_SHIP_BEAM
    mask: pygame.Mask = pygame.mask.from_surface(ship_img)
    max_health: int = 100
    
    def move_lasers(self, velocity: int, objs: list[GameObj]):
        self.cooldown()
        for laser in self.lasers[:]:
            laser.move(velocity)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs[:]:
                    if laser.collision(obj):
                        self.lasers.remove(laser)
                        objs.remove(obj)
    
    def healthbar(self, window):
        hbar_width = self.ship_img.get_width()
        health_ratio = self.health / self.max_health
        hbar_xpos = self.x
        hbar_ypos = self.y + self.ship_img.get_height() + 10
        pygame.draw.rect(window, "red", (hbar_xpos, hbar_ypos, hbar_width, 5))
        pygame.draw.rect(window, "green", (hbar_xpos, hbar_ypos,hbar_width * health_ratio, 5))
        

@dataclass
class Enemy(Ship):
    BEAM_MAP: ClassVar[dict[str, pygame.Surface]] = {
        "small": SMALL_ENEMY_BEAM,
        "big": BIG_ENEMY_BEAM
    }
    SHIP_MAP: ClassVar[dict[str, pygame.Surface]] = {
        "easy": EASY_ENEMY_SHIP,
        "medium": MEDIUM_ENEMY_SHIP,
        "hard": HARD_ENEMY_SHIP
    }
    
    ship_type: str = "enemy"
    ship: str = "easy"
    beam: str = "small"
    ship_img: pygame.Surface = SHIP_MAP[ship]
    laser_img: pygame.Surface = BEAM_MAP[beam]
    mask: pygame.Mask = pygame.mask.from_surface(ship_img)
    
    def move(self, velocity):
        self.y += velocity


def collide(obj1: GameObj, obj2: GameObj):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


def main():
    running = True
    lost = False
    lost_count = 0
    FPS = 60
    level = 0
    lives = 3
    main_font = pygame.font.SysFont('comicsans', 20)
    lost_font = pygame.font.SysFont('comicsans', 60)
    
    enemies: list[Enemy] = []
    wave_length = 5
    enemy_velocity = 1
    laser_velocity = 4
    
    player = Player((WIDTH - PLAYER_SHIP.get_width()) / 2, HEIGHT - PLAYER_SHIP.get_height() - 20)
    player_velocity = 5
    
    clock = pygame.time.Clock()
    
    def redraw_window() -> None:
        # Draw the background
        WINDOW.blit(SPACE_BACKGROUND, (0, 0))
        
        # Draw the text on the window
        lives_label = main_font.render(f"Lives: {lives}", 1, "white")
        level_label = main_font.render(f"Level: {level}", 1, "white")
        
        WINDOW.blit(lives_label, (10, 10))
        WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        
        for enemy in enemies:
            enemy.draw(WINDOW)
        
        player.draw(WINDOW)
        player.healthbar(WINDOW)
        
        if lost:
            lost_label = lost_font.render("Game over! Try again", 1, "red")
            WINDOW.blit(lost_label, ((WIDTH - lost_label.get_width()) / 2, (HEIGHT - lost_label.get_height()) / 2))
        
        pygame.display.update()
    
    while running:
        # Update the window
        redraw_window()
        
        # Init the clock on the device for the game
        clock.tick(FPS)
        
        if lives <= 0 or player.health <= 0:
            lost = True
            lost_count += 1
        
        if lost:
            if lost_count > FPS * 3:
                running = False
            else:
                continue
        
        if len(enemies) == 0:
            level += 1
            wave_length += 5
            for i in range(wave_length):
                x = random.randrange(50, WIDTH-100)
                y = random.randrange(-2 * HEIGHT * level // 5, -100)
                ship=random.choice(["easy", "medium", "hard"])
                match ship:
                    case "easy":
                        beam = "small"
                    case "medium":
                        beam = random.choice(["small", "big"])
                    case "hard":
                        beam = "big"
                enemy = Enemy(x, y, ship=ship, beam=beam)
                enemies.append(enemy)
        
        # Check if event are happening
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                
        keys = pygame.key.get_pressed()
        if (keys[pygame.K_q] or keys[pygame.K_LEFT]) and player.x - player_velocity > 0: # left
            player.x -= player_velocity
        if (keys[pygame.K_d] or keys[pygame.K_RIGHT]) and player.x + player_velocity + player.get_width() < WIDTH: # right
            player.x += player_velocity
        if (keys[pygame.K_z] or keys[pygame.K_UP]) and player.y - player_velocity > 0: # up
            player.y -= player_velocity
        if (keys[pygame.K_s] or keys[pygame.K_DOWN]) and player.y + player_velocity + player.get_height() + 20 < HEIGHT: # down
            player.y += player_velocity
        if keys[pygame.K_SPACE]:
            player.shoot()
        
        for enemy in enemies[:]:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_velocity, player)
            
            if random.randrange(0, FPS * (11 - level)) == 1:
                enemy.shoot()
            if collide(enemy, player):
                player.health -= 10
                enemies.remove(enemy)
            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)
        
        player.move_lasers(-laser_velocity, enemies)
        
def main_menu():
    title_font = pygame.font.SysFont("comicsans", 50)
    running = True
    
    while running:
        WINDOW.blit(SPACE_BACKGROUND, (0, 0))
        title_label = title_font.render("Press the mouse to begin...", 1, "white")
        WINDOW.blit(title_label, ((WIDTH - title_label.get_width()) / 2, (HEIGHT - title_label.get_height()) / 2))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                main()
                
    pygame.quit()

main_menu()