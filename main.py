from win32api import GetSystemMetrics
import pygame
import random
import os

from assets import Player, Enemy, ShipType, LaserType, collide, get_image_size
from button import Button

# Init the font of the pygame window
pygame.font.init()

# Init the pygame window
WIDTH = GetSystemMetrics(0)
HEIGHT = GetSystemMetrics(1) - 60
WINDOW = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invader game")

# Load images
MENU_BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("backgrounds", "menu_background.png")), (WIDTH, HEIGHT))
GAME_BACKGROUND = pygame.transform.scale(pygame.image.load(os.path.join("backgrounds", "game_bg_1.png")), (WIDTH, HEIGHT))


def get_font(size: int) -> pygame.font.Font:
    return pygame.font.Font("assets/font.ttf", size)

def play(game_bg: pygame.Surface):
    running = True
    lost = False
    win = False
    lost_count = 0
    win_count = 0
    FPS = 60
    level = 0
    lives = 3
    
    enemies: list[Enemy] = []
    wave_length = 5
    enemy_velocity = 1
    laser_velocity = 4
    
    player = Player((WIDTH - get_image_size("large", "ship")[0]) / 2, HEIGHT - get_image_size("large", "ship")[1] - 20)
    player_velocity = 8
    
    clock = pygame.time.Clock()
    
    def redraw_window() -> None:
        # Draw the background
        WINDOW.blit(game_bg, (0, 0))
        
        # Draw the text on the window
        lives_label = get_font(20).render(f"Lives: {lives}", 1, "white")
        level_label = get_font(20).render(f"Level: {level}", 1, "white")
        
        WINDOW.blit(lives_label, (10, 10))
        WINDOW.blit(level_label, (WIDTH - level_label.get_width() - 10, 10))
        
        for enemy in enemies:
            enemy.draw(WINDOW)
        
        player.draw(WINDOW)
        player.healthbar(WINDOW)
        
        if win:
            congrat_label = get_font(60).render("Congratulation!", 1, "green")
            WINDOW.blit(congrat_label, ((WIDTH - congrat_label.get_width()) / 2, (HEIGHT - congrat_label.get_height()) / 2 - 40))
            win_label = get_font(60).render("You finished the game", 1, "green")
            WINDOW.blit(win_label, ((WIDTH - win_label.get_width()) / 2, (HEIGHT - win_label.get_height()) / 2 + 40))
        
        if lost:
            lost_label = get_font(60).render("Game over! Try again", 1, "red")
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
                main_menu(game_bg)
            else:
                continue
            
        if level == 10 and len(enemies) == 0:
            win = True
            win_count += 1
        
        if win:
            if win_count > FPS * 3:
                main_menu(game_bg)
            else:
                continue
        
        if len(enemies) == 0:
            level += 1
            for i in range(wave_length):
                x = random.randrange(50, WIDTH-100)
                y = random.randrange(-2 * HEIGHT * level // 5, -100)
                ship_type=random.choice(list(ShipType))
                match ship_type:
                    case ShipType.SMALL:
                        laser = LaserType.NORMAL
                    case ShipType.MEDIUM:
                        laser = random.choice(list(LaserType))
                    case ShipType.LARGE:
                        laser = LaserType.NORMAL
                enemy = Enemy(x, y, ship_type=ship_type, laser_type=laser)
                enemies.append(enemy)
            
            wave_length += 5
        
        # Check if event are happening
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
                
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
        if keys[pygame.K_ESCAPE]:
            main_menu(game_bg)
        
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
        
    pygame.quit()

def options(game_bg: pygame.Surface):
    running = True
    
    def change_game_bg(bg: pygame.Surface):
        return pygame.transform.scale(bg, (WIDTH, HEIGHT))
    
    while running:
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        
        LIST_BG_BTN: list[Button] = []
        LIST_BG: list[pygame.Surface] = []
        
        WINDOW.blit(MENU_BACKGROUND, (0, 0))
        MENU_TEXT = get_font(WIDTH//20).render("OPTIONS", 1, "#04BBFF")
        MENU_RECT = MENU_TEXT.get_rect(center=(WIDTH//2, HEIGHT//15))
        WINDOW.blit(MENU_TEXT, MENU_RECT)
        
        for i, bg in enumerate(os.listdir(os.path.join("backgrounds"))[:-1]):
            LIST_BG_BTN.append(Button(image_path=os.path.join("assets", "button_rect.png"), pos= (WIDTH //3, 220+i*75), transform=True,
                                  font=get_font(20), base_color="#D7FCD4", hovering_color="white", text_input=f"Background {i+1}"))
            LIST_BG.append(pygame.transform.scale(pygame.image.load(os.path.join("backgrounds", bg)), (560, 350)))
            
        for button in LIST_BG_BTN:
            button.change_color(MENU_MOUSE_POS)
            button.update(WINDOW)
        CURRENT_GAME_BG = pygame.transform.scale(game_bg, (560, 350))
        WINDOW.blit(CURRENT_GAME_BG, CURRENT_GAME_BG.get_rect(center=(2*WIDTH//3, HEIGHT//2-25)))
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                for i, btn in enumerate(LIST_BG_BTN):
                    if btn.check_input(MENU_MOUSE_POS):
                        game_bg = change_game_bg(LIST_BG[i])
                        pygame.display.update()

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            main_menu(game_bg)
                
    pygame.quit()

def main_menu(game_bg: pygame.Surface):
    running = True
    
    while running:
        MENU_MOUSE_POS = pygame.mouse.get_pos()
        
        WINDOW.blit(MENU_BACKGROUND, (0, 0))
        MENU_TEXT = get_font(WIDTH//20).render("MAIN MENU", 1, "#04BBFF")
        MENU_RECT = MENU_TEXT.get_rect(center=(WIDTH//2, HEIGHT//15))
        WINDOW.blit(MENU_TEXT, MENU_RECT)
        
        PLAY_BUTTON = Button(image_path=os.path.join("assets", "button_rect.png"), pos=(WIDTH//2, 6*HEIGHT//20),
                             base_color="#D7FCD4", hovering_color="white", font=get_font(50), text_input="PLAY")
        OPTIONS_BUTTON = Button(image_path=os.path.join("assets", "button_rect.png"), pos=(WIDTH//2, 9*HEIGHT//20),
                                base_color="#D7FCD4", hovering_color="white", font=get_font(50), text_input="OPTIONS")
        QUIT_BUTTON = Button(image_path=os.path.join("assets", "button_rect.png"), pos=(WIDTH//2, 12*HEIGHT//20),
                             base_color="#D7FCD4", hovering_color="white", font=get_font(50), text_input="EXIT")
        
        for button in [PLAY_BUTTON, OPTIONS_BUTTON, QUIT_BUTTON]:
            button.change_color(MENU_MOUSE_POS)
            button.update(WINDOW)
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if PLAY_BUTTON.check_input(MENU_MOUSE_POS):
                    play(game_bg)
                if OPTIONS_BUTTON.check_input(MENU_MOUSE_POS):
                    options(game_bg)
                if QUIT_BUTTON.check_input(MENU_MOUSE_POS):
                    quit()
                
    pygame.quit()

main_menu(GAME_BACKGROUND)