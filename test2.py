import pygame
import random
from enum import Enum
import math
from pygame import mixer

# Initialize Pygame and Mixer for audio
pygame.init()
mixer.init()

# Constants
class GameState(Enum):
    MENU = "menu"
    SELECTING = "selecting"
    SHOW_CHOICES = "show_choices"
    MINUS_ONE = "minus_one"
    RESULT = "result"
    BATTLE = "battle"
    GAME_OVER = "game_over"

class Colors:
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (200, 0, 0)
    RED_HOVER = (255, 100, 100)
    BLUE = (0, 0, 200)
    BLUE_HOVER = (100, 100, 255)
    GREEN = (0, 200, 0)
    GREEN_HOVER = (100, 255, 100)
    GRAY = (180, 180, 180)
    GRAY_HOVER = (220, 220, 220)

# Screen setup
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Rock Paper Scissors Minus One")

# Fonts
FONT = pygame.font.Font(None, 36)
BIG_FONT = pygame.font.Font(None, 48)

# Load Images
def load_image(filename):
    try:
        image = pygame.image.load(filename)
        return pygame.transform.scale(image, (150, 150))
    except pygame.error as e:
        print(f"Error loading {filename}: {e}")
        pygame.quit()
        exit()

def load_sound(filename):
    try:
        return mixer.Sound(filename)
    except pygame.error as e:
        print(f"Warning: Could not load {filename}: {e}")
        return None

ROCK_IMG = load_image("rock.png")
PAPER_IMG = load_image("paper.png")
SCISSORS_IMG = load_image("scissors.png")
BACKGROUND = pygame.transform.scale(pygame.image.load("background.jpg").convert(), (WIDTH, HEIGHT))
IMAGES = {"Rock": ROCK_IMG, "Paper": PAPER_IMG, "Scissors": SCISSORS_IMG}

# Audio (loaded dynamically to avoid initial errors)
bg_music = None
select_sound = None
battle_sound = None
win_sound = None
lose_sound = None

# Particle class for effects
class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = random.randint(5, 10)
        self.color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        self.life = random.randint(20, 40)

    def update(self):
        self.life -= 1
        self.x += random.uniform(-2, 2)
        self.y += random.uniform(-2, 2)
        return self.life > 0

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

particles = []

# Button Class
class Button:
    def __init__(self, x, y, width, height, text, color, hover_color, callback=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.callback = callback

    def draw(self, screen):
        mouse_pos = pygame.mouse.get_pos()
        color = self.hover_color if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        text_surface = FONT.render(self.text, True, Colors.BLACK)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if (event.type == pygame.MOUSEBUTTONDOWN and 
            self.rect.collidepoint(event.pos) and 
            self.callback):
            self.callback()
            return True
        return False

# Game Setup
OPTIONS = ["Rock", "Paper", "Scissors"]
player_hands = []
computer_hands = []
user_sets_won = 0
computer_sets_won = 0
current_set = 1
max_sets = 1
wins_needed = 1
game_state = GameState.MENU
clock = pygame.time.Clock()
player_removed = None
computer_removed = None

# Animation variables
battle_timer = 0
player_x = 100
computer_x = WIDTH - 250
battle_complete = False
fade_alpha = 0
game_over_surface = None  # Surface to hold GAME_OVER display

# Buttons initialization
def start_game(sets):
    global max_sets, game_state, wins_needed, fade_alpha, bg_music, select_sound, battle_sound, win_sound, lose_sound, game_over_surface
    max_sets = sets
    wins_needed = (sets + 1) // 2
    game_state = GameState.SELECTING
    fade_alpha = 255  # Start with fade-in effect
    mixer.stop()  # Stop any previous audio
    bg_music = load_sound("background_music.mp3")
    select_sound = load_sound("select.wav")
    battle_sound = load_sound("battle.wav")
    win_sound = load_sound("win.wav")
    lose_sound = load_sound("lose.wav")
    player_hands.clear()
    computer_hands.clear()
    player_removed = None
    computer_removed = None
    user_sets_won = 0
    computer_sets_won = 0
    current_set = 1
    game_over_surface = None  # Reset game over surface

def reset_game():
    global game_state, user_sets_won, computer_sets_won, current_set, game_over_surface
    game_state = GameState.MENU
    user_sets_won = 0
    computer_sets_won = 0
    current_set = 1
    game_over_surface = None  # Reset game over surface
    if select_sound and not select_sound.get_num_channels():  # Restart select music
        select_sound.play(-1)

CHOICE_BUTTONS = [
    Button(100, 400, 150, 50, "Rock", Colors.RED, Colors.RED_HOVER, 
           lambda: player_hands.append("Rock") if len(player_hands) < 2 else None),
    Button(325, 400, 150, 50, "Paper", Colors.BLUE, Colors.BLUE_HOVER,
           lambda: player_hands.append("Paper") if len(player_hands) < 2 else None),
    Button(550, 400, 150, 50, "Scissors", Colors.GREEN, Colors.GREEN_HOVER,
           lambda: player_hands.append("Scissors") if len(player_hands) < 2 else None)
]

MENU_BUTTONS = [
    Button(100, 200, 150, 50, "Best of 1", Colors.GRAY, Colors.GRAY_HOVER, lambda: start_game(1)),
    Button(325, 200, 150, 50, "Best of 3", Colors.GRAY, Colors.GRAY_HOVER, lambda: start_game(3)),
    Button(550, 200, 150, 50, "Best of 5", Colors.GRAY, Colors.GRAY_HOVER, lambda: start_game(5))
]

GAME_OVER_BUTTON = Button(WIDTH//2 - 75, 400, 150, 50, "NEW GAME", Colors.GRAY, Colors.GRAY_HOVER, reset_game)

# Game Logic
def determine_winner(player, computer):
    if player == computer:
        return "Tie"
    winning_combos = {("Rock", "Scissors"), ("Paper", "Rock"), ("Scissors", "Paper")}
    return "Player" if (player, computer) in winning_combos else "Computer"

def add_particles(x, y, count=20):
    for _ in range(count):
        particles.append(Particle(x, y))

# Main game loop
running = True
keep_buttons = []

while running:
    screen.blit(BACKGROUND, (0, 0))  # Background image
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if game_state == GameState.MENU:
            for button in MENU_BUTTONS:
                button.handle_event(event)
            if select_sound and not select_sound.get_num_channels():  # Play select music at start
                select_sound.play(-1)
                
        elif game_state == GameState.SELECTING:
            for button in CHOICE_BUTTONS:
                button.handle_event(event)
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and 
                len(player_hands) == 2):
                mixer.stop()  # Stop select music
                if battle_sound:
                    battle_sound.play(-1)  # Loop battle music
                computer_hands = random.sample(OPTIONS, 2)
                game_state = GameState.SHOW_CHOICES
                
        elif game_state == GameState.SHOW_CHOICES:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                keep_buttons = [
                    Button(200, 400, 150, 50, player_hands[0], Colors.GRAY, Colors.GRAY_HOVER,
                           lambda: (globals().update({'player_removed': player_hands.pop(1), 'game_state': GameState.RESULT}))),
                    Button(360, 400, 150, 50, player_hands[1], Colors.GRAY, Colors.GRAY_HOVER,
                           lambda: (globals().update({'player_removed': player_hands.pop(0), 'game_state': GameState.RESULT})))
                ]
                game_state = GameState.MINUS_ONE
                
        elif game_state == GameState.MINUS_ONE:
            for button in keep_buttons:
                if button.handle_event(event):
                    computer_removed = computer_hands.pop(random.randrange(len(computer_hands)))
                    keep_buttons.clear()
                    add_particles(WIDTH//2, HEIGHT//2, 30)  # Particle effect on selection
                    
        elif game_state == GameState.RESULT:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                battle_timer = 0
                player_x = 100
                computer_x = WIDTH - 250
                battle_complete = False
                game_state = GameState.BATTLE
                
        elif game_state == GameState.BATTLE:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN and battle_complete:
                winner = determine_winner(player_hands[0], computer_hands[0])
                if winner == "Player":
                    user_sets_won += 1
                elif winner == "Computer":
                    computer_sets_won += 1
                mixer.stop()  # Stop battle music
                if winner == "Player" and win_sound:
                    win_sound.play()
                elif winner == "Computer" and lose_sound:
                    lose_sound.play()
                elif winner == "Tie" and select_sound:
                    mixer.stop()  # Stop battle music on tie
                    select_sound.play(-1)  # Resume select music for next set
                if user_sets_won >= wins_needed or computer_sets_won >= wins_needed:
                    game_state = GameState.GAME_OVER
                else:
                    current_set += 1
                    player_hands.clear()
                    computer_hands.clear()
                    player_removed = None
                    computer_removed = None
                    game_state = GameState.SELECTING

        elif game_state == GameState.GAME_OVER:
            if game_over_surface is None:
                game_over_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                game_over_surface.fill((0, 0, 0, 200))  # Semi-transparent black overlay
                text = BIG_FONT.render("GAME WON" if user_sets_won >= wins_needed else "GAME OVER", True, 
                                      Colors.GREEN if user_sets_won >= wins_needed else Colors.RED)
                game_over_surface.blit(text, text.get_rect(center=(WIDTH//2, 200)))
                if user_sets_won >= wins_needed:
                    text = BIG_FONT.render(f"You Won the Set {user_sets_won}-{computer_sets_won}!", True, Colors.GREEN)
                elif computer_sets_won >= wins_needed:
                    text = BIG_FONT.render(f"CPU Won the Set {computer_sets_won}-{user_sets_won}!", True, Colors.RED)
                game_over_surface.blit(text, text.get_rect(center=(WIDTH//2, 300)))
                GAME_OVER_BUTTON.draw(game_over_surface)
            screen.blit(game_over_surface, (0, 0))
            if GAME_OVER_BUTTON.handle_event(event):
                reset_game()
                game_over_surface = None  # Clear surface after reset

    # Rendering and Animation
    if game_state == GameState.MENU:
        text = BIG_FONT.render("Choose Best of:", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 100)))
        for button in MENU_BUTTONS:
            button.draw(screen)
        
    elif game_state == GameState.SELECTING:
        text = BIG_FONT.render(f"Set {current_set}: Choose Two Hands", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 100)))
        for button in CHOICE_BUTTONS:
            button.draw(screen)
        if len(player_hands) == 2:
            text = FONT.render("Hands Selected! Press SPACE", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 500)))
            
    elif game_state == GameState.SHOW_CHOICES:
        text = BIG_FONT.render("Both Players Chose!", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 50)))
        
        # Position player's options on the far left
        for i, player_hand in enumerate(player_hands):
            screen.blit(IMAGES[player_hand], (50 + i*180, 250))  # Far left, spaced out
        
        # Position computer's options on the far right, within screen bounds
        for i, comp_hand in enumerate(computer_hands):
            screen.blit(IMAGES[comp_hand], (WIDTH - 350 + i*180, 250))  # Far right, spaced out, within 800px
        
        text = FONT.render("Press SPACE to remove one hand", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 500)))
        
    elif game_state == GameState.MINUS_ONE:
        text = BIG_FONT.render("Choose Hand to Keep!", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 50)))
        for i, hand in enumerate(player_hands):
            screen.blit(IMAGES[hand], (200 + i*120, 250))
        for button in keep_buttons:
            button.draw(screen)
            
    elif game_state == GameState.RESULT:
        text = BIG_FONT.render(f"Set {current_set} Result", True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 50)))
        
        if (player_hands and len(player_hands) == 1 and 
            computer_hands and len(computer_hands) == 1 and 
            player_removed and computer_removed):
            text = FONT.render(f"You removed: {player_removed}", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 120)))
            text = FONT.render(f"CPU removed: {computer_removed}", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 150)))
            
            text = FONT.render("Final:", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 200)))
            
            # Position player's final option on the far left
            if player_hands[0] in IMAGES:
                screen.blit(IMAGES[player_hands[0]], (50, 230))  # Far left, within screen
            
            # Position computer's final option on the far right
            if computer_hands[0] in IMAGES:
                screen.blit(IMAGES[computer_hands[0]], (650, 230))  # Far right, within screen
            
            text = FONT.render("Press SPACE for Battle!", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 450)))
        
        text = FONT.render(f"Best of {max_sets}: You {user_sets_won} - {computer_sets_won} CPU", 
                          True, Colors.BLACK)
        screen.blit(text, text.get_rect(center=(WIDTH//2, 350)))
        
    elif game_state == GameState.BATTLE:
        winner = determine_winner(player_hands[0], computer_hands[0])
        battle_timer += 1
        
        if battle_timer < 60:
            player_x += (WIDTH/2 - 250 - player_x) * 0.1
            computer_x += (WIDTH/2 + 100 - computer_x) * 0.1
        elif battle_timer < 90 and winner != "Tie":
            if winner == "Player":
                player_x += 10
            else:
                computer_x -= 10
        elif battle_timer >= 90:
            battle_complete = True
        
        if battle_timer < 90 or winner == "Tie" or winner == "Player":
            screen.blit(IMAGES[player_hands[0]], (player_x, HEIGHT//2 - 75))
        if battle_timer < 90 or winner == "Tie" or winner == "Computer":
            screen.blit(IMAGES[computer_hands[0]], (computer_x, HEIGHT//2 - 75))
        
        if battle_complete:
            winner_text = "Tie Game!" if winner == "Tie" else f"{winner} Wins!"
            text = FONT.render(winner_text, True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 150)))
            
            text = FONT.render(f"Best of {max_sets}: You {user_sets_won} - {computer_sets_won} CPU", 
                              True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 200)))
            
            text = FONT.render("Press ENTER for next set", True, Colors.BLACK)
            screen.blit(text, text.get_rect(center=(WIDTH//2, 500)))

    # Particle effects
    for particle in particles[:]:
        if particle.update():
            particle.draw(screen)
        else:
            particles.remove(particle)

    # Fade effect for transitions
    if fade_alpha > 0:
        fade_surface = pygame.Surface((WIDTH, HEIGHT))
        fade_surface.fill((0, 0, 0))
        fade_surface.set_alpha(fade_alpha)
        screen.blit(fade_surface, (0, 0))
        fade_alpha = max(0, fade_alpha - 5)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()