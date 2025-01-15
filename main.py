import pygame
import numpy as np
import random
import math
from PIL import Image

# Initialize Pygame
pygame.init()
pygame.font.init()

# Constants
WINDOW_WIDTH = 1080
WINDOW_HEIGHT = 640
DOT_RADIUS = 8
BONUS_RADIUS = 6
GLOBAL_MIN_SPEED = 0.1
GLOBAL_MAX_SPEED = 1.2
MIN_SPEED_RANGE = 0.3  # Minimum gap between min and max speed of a dot
EATING_DISTANCE = 12  # Reduced from 15 to make eating harder
CHASE_THRESHOLD = 300  # Reduced from 400 to make chasing more strategic
FLEE_THRESHOLD = 150  # Increased from 100 to make dots more cautious
INITIAL_DOTS_PER_GROUP = 90
CIRCLE_SHRINK_SPEED = 0.4  # Reduced from 0.6 to give more time for strategy
OUTSIDE_CIRCLE_FORCE = 8  # Reduced from 10 to make boundary less harsh
INITIAL_CIRCLE_RADIUS = 650
RESTART_DELAY = 5000  # 5 seconds in milliseconds

# Colors (Monet-inspired palette)
WATER_BLUE = (142, 190, 216)     # Light blue from water lilies
LILY_PINK = (255, 182, 193)      # Soft pink from lilies
LEAF_GREEN = (144, 169, 85)      # Muted green from leaves
SUNSET_GOLD = (255, 215, 150)    # Warm gold from sunsets
LAVENDER = (230, 230, 250)       # Soft purple from flowers
DEEP_BLUE = (25, 25, 112)        # Deep blue from evening scenes
SOFT_WHITE = (245, 245, 245)     # Soft white for highlights

# Game colors
RED = LILY_PINK
GREEN = LEAF_GREEN
BLUE = WATER_BLUE
BLACK = DEEP_BLUE
WHITE = SOFT_WHITE
CIRCLE_COLOR = LAVENDER
PURPLE = (180, 160, 210)    # Softer purple for bonus disks
YELLOW = SUNSET_GOLD

# Speed distribution parameters
POISSON_MEAN_A = 1.2  # Mean for group A's max speed
POISSON_MEAN_B = 1.0  # Mean for group B's max speed
POISSON_MEAN_C = 0.8  # Mean for group C's max speed

# Font setup
FONT_LARGE = pygame.font.Font(None, 74)
FONT_MEDIUM = pygame.font.Font(None, 48)

class Dot:
    def __init__(self, x, y, group):
        self.x = x
        self.y = y
        self.group = group
        self.target = None
        
        # Initialize speed range based on Poisson distribution
        poisson_means = {
            'A': POISSON_MEAN_A,
            'B': POISSON_MEAN_B,
            'C': POISSON_MEAN_C
        }
        
        # Generate max speed using Poisson distribution
        max_speed = min(GLOBAL_MAX_SPEED, 
                       max(GLOBAL_MIN_SPEED + MIN_SPEED_RANGE,
                           np.random.poisson(poisson_means[group]) / 5))  # Divide by 5 to scale to our speed range
        
        # Generate min speed ensuring minimum gap
        available_min = max(GLOBAL_MIN_SPEED, max_speed - 1.4)  # Ensure within global range
        available_max = max_speed - MIN_SPEED_RANGE  # Ensure minimum gap
        self.min_speed = random.uniform(available_min, available_max)
        self.max_speed = max_speed
        
        # Initialize current speed within the dot's range
        self.speed = random.uniform(self.min_speed, self.max_speed)
        self.base_speed = self.speed  # Store original speed for reference
        
        self.direction = random.uniform(0, 2 * math.pi)
        self.fleeing = False
        self.bonus_target = None
        self.momentum_x = 0
        self.momentum_y = 0
        self.momentum_decay = 0.95
        self.stalemate_timer = 0
        self.last_angle = 0
        self.bonus_multiplier = 1
        self.bonus_time = 0
        self.game_dots = []
        self.strategic_timer = 0  # Timer for strategic decision making

    def get_image(self):
        return {
            'A': Game.scissors_img,
            'B': Game.paper_img,
            'C': Game.rock_img
        }[self.group]

    def can_eat(self, other):
        return (
            (self.group == 'A' and other.group == 'B') or
            (self.group == 'B' and other.group == 'C') or
            (self.group == 'C' and other.group == 'A')
        )

    def distance_to(self, other):
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def count_population(self):
        populations = {'A': 0, 'B': 0, 'C': 0}
        for dot in self.game_dots:
            populations[dot.group] += 1
        return populations

    def should_be_strategic(self, populations):
        # Get the group that this dot can eat
        prey_group = {'A': 'B', 'B': 'C', 'C': 'A'}[self.group]
        # Get the group that can eat this dot
        predator_group = {'A': 'C', 'B': 'A', 'C': 'B'}[self.group]
        
        total_dots = sum(populations.values())
        if total_dots == 0:
            return False
            
        prey_ratio = populations[prey_group] / total_dots
        predator_ratio = populations[predator_group] / total_dots
        my_ratio = populations[self.group] / total_dots
        
        # Enhanced strategic conditions
        CRITICAL_POPULATION = 15  # Increased threshold for strategic behavior
        CRITICAL_RATIO = 0.25    # Increased ratio threshold
        ULTRA_PROTECTIVE_THRESHOLD = 8  # New threshold for ultra-protective behavior
        
        return (
            populations[prey_group] < CRITICAL_POPULATION or  # Prey population is low
            prey_ratio < CRITICAL_RATIO or                   # Prey ratio is low
            predator_ratio > 0.4 or                         # Many predators
            min(populations.values()) < ULTRA_PROTECTIVE_THRESHOLD or  # Any group is endangered
            my_ratio > 0.5 or                              # We're becoming too dominant
            abs(populations[prey_group] - populations[predator_group]) < 5  # Balance is delicate
        )

    def get_strategic_movement(self, target_dx, target_dy, distance, populations):
        dx = dy = 0
        prey_group = {'A': 'B', 'B': 'C', 'C': 'A'}[self.group]
        
        # Calculate the center of the arena
        center_x = WINDOW_WIDTH / 2
        center_y = WINDOW_HEIGHT / 2
        
        # More sophisticated strategic movement
        if populations[prey_group] < ULTRA_PROTECTIVE_THRESHOLD:  # Ultra-protective of last few prey
            if distance < CHASE_THRESHOLD:
                # Actively avoid the last remaining prey
                dx = -(target_dx/distance) * self.speed * 1.2
                dy = -(target_dy/distance) * self.speed * 1.2
                
                # Move towards the center if too far from it
                to_center_x = center_x - self.x
                to_center_y = center_y - self.y
                center_dist = math.sqrt(to_center_x**2 + to_center_y**2)
                if center_dist > WINDOW_WIDTH/4:
                    dx += (to_center_x/center_dist) * self.speed * 0.4
                    dy += (to_center_y/center_dist) * self.speed * 0.4
        
        elif populations[prey_group] < CRITICAL_POPULATION:  # Protective behavior
            if distance < EATING_DISTANCE * 4:
                # Move sideways relative to prey
                perpendicular_x = -target_dy/distance
                perpendicular_y = target_dx/distance
                dx = perpendicular_x * self.speed * 0.8
                dy = perpendicular_y * self.speed * 0.8
            elif distance < CHASE_THRESHOLD:
                # Maintain distance without approaching
                dx = (target_dx/distance) * self.speed * 0.2
                dy = (target_dy/distance) * self.speed * 0.2
        
        else:  # Normal strategic behavior
            if distance < CHASE_THRESHOLD:
                # Keep moderate distance and move more unpredictably
                dx = (target_dx/distance) * self.speed * 0.4
                dy = (target_dy/distance) * self.speed * 0.4
                
                # Add circular movement
                if random.random() < 0.3:
                    perpendicular_x = -target_dy/distance
                    perpendicular_y = target_dx/distance
                    dx += perpendicular_x * self.speed * 0.3
                    dy += perpendicular_y * self.speed * 0.3
        
        # Add some randomness to prevent predictable patterns
        if random.random() < 0.15:
            dx += random.uniform(-0.3, 0.3) * self.speed
            dy += random.uniform(-0.3, 0.3) * self.speed
        
        return dx, dy

    def adjust_speed(self):
        # Randomly adjust speed within dot's personal range
        if random.random() < 0.05:  # 5% chance to change speed each frame
            speed_change = random.uniform(-0.1, 0.1)
            new_speed = self.speed + speed_change
            # Ensure speed stays within dot's personal range
            self.speed = max(self.min_speed, min(self.max_speed, new_speed))

    def move_towards_target(self):
        # Add speed adjustment at the start of movement
        self.adjust_speed()
        
        populations = self.count_population()
        being_strategic = self.should_be_strategic(populations)
        
        base_movement_x = math.cos(self.direction) * self.speed * 0.3
        base_movement_y = math.sin(self.direction) * self.speed * 0.3

        dx = dy = 0

        nearby_groups = set()
        for dot in self.game_dots:
            if dot != self and self.distance_to(dot) < CHASE_THRESHOLD * 0.5:
                nearby_groups.add(dot.group)

        if len(nearby_groups) == 2 and self.group not in nearby_groups:
            self.stalemate_timer += 1
        else:
            self.stalemate_timer = max(0, self.stalemate_timer - 1)

        if self.stalemate_timer > 60:
            if random.random() < 0.1:
                burst_angle = random.uniform(0, 2 * math.pi)
                self.momentum_x += math.cos(burst_angle) * self.speed * 2
                self.momentum_y += math.sin(burst_angle) * self.speed * 2
                self.stalemate_timer = 0

        if self.bonus_target:
            bonus_dx = self.bonus_target.x - self.x
            bonus_dy = self.bonus_target.y - self.y
            bonus_dist = math.sqrt(bonus_dx**2 + bonus_dy**2)
            if bonus_dist > 0:
                dx = (bonus_dx/bonus_dist) * self.speed * 1.5
                dy = (bonus_dy/bonus_dist) * self.speed * 1.5
        elif self.target is not None:
            nearest_predator = None
            nearest_pred_dist = float('inf')
            for dot in self.game_dots:
                if dot.can_eat(self):
                    pred_dist = self.distance_to(dot)
                    if pred_dist < nearest_pred_dist:
                        nearest_predator = dot
                        nearest_pred_dist = pred_dist

            if nearest_predator and nearest_pred_dist < FLEE_THRESHOLD:
                self.fleeing = True
                flee_dx = self.x - nearest_predator.x
                flee_dy = self.y - nearest_predator.y
                flee_dist = math.sqrt(flee_dx**2 + flee_dy**2)
                if flee_dist > 0:
                    flee_multiplier = random.uniform(0.8, 1.2)
                    dx = (flee_dx/flee_dist) * self.speed * flee_multiplier
                    dy = (flee_dy/flee_dist) * self.speed * flee_multiplier
            else:
                self.fleeing = False
                target_dx = self.target.x - self.x
                target_dy = self.target.y - self.y
                distance = math.sqrt(target_dx**2 + target_dy**2)

                if self.can_eat(self.target):
                    if being_strategic:
                        # Get strategic movement based on population state
                        dx, dy = self.get_strategic_movement(target_dx, target_dy, distance, populations)
                    else:
                        # Normal hunting behavior
                        if distance > 0 and distance < CHASE_THRESHOLD:
                            dx = (target_dx/distance) * self.speed
                            dy = (target_dy/distance) * self.speed

        # Add some randomness to movement when being strategic
        if being_strategic:
            if random.random() < 0.15:  # Increased randomness
                dx += random.uniform(-0.7, 0.7) * self.speed  # More random movement
                dy += random.uniform(-0.7, 0.7) * self.speed

        self.momentum_x = self.momentum_x * self.momentum_decay
        self.momentum_y = self.momentum_y * self.momentum_decay

        self.momentum_x += random.uniform(-0.1, 0.1) * self.speed
        self.momentum_y += random.uniform(-0.1, 0.1) * self.speed

        self.x += base_movement_x + dx + self.momentum_x
        self.y += base_movement_y + dy + self.momentum_y

        if self.x <= DOT_RADIUS or self.x >= WINDOW_WIDTH - DOT_RADIUS:
            self.direction = math.pi - self.direction
            self.x = max(DOT_RADIUS, min(WINDOW_WIDTH - DOT_RADIUS, self.x))

        if self.y <= DOT_RADIUS or self.y >= WINDOW_HEIGHT - DOT_RADIUS:
            self.direction = -self.direction
            self.y = max(DOT_RADIUS, min(WINDOW_HEIGHT - DOT_RADIUS, self.y))

    def apply_bonus(self):
        self.bonus_multiplier = 5
        self.bonus_time = pygame.time.get_ticks()

    def update_bonus(self):
        if self.bonus_multiplier > 1:
            current_time = pygame.time.get_ticks()
            if current_time - self.bonus_time > 5000:  
                self.bonus_multiplier = 1

class BonusDisk:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = BONUS_RADIUS
        self.color = PURPLE

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Scissors-Paper-Rock Battlefield")
        self.reset_game()

    def reset_game(self):
        # Load and scale images
        self.load_images()
        
        self.clock = pygame.time.Clock()
        self.dots = []
        self.circle_center = (WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)
        self.circle_radius = INITIAL_CIRCLE_RADIUS
        self.bonus_disks = []
        self.bonus_spawned = {
            0.7: False,
            0.8: False,
            0.6: False,
            0.4: False
        }
        self.winner = None
        self.winner_time = 0
        self.font = pygame.font.Font(None, 24)  # Add font for status table
        self.initialize_dots()
        for dot in self.dots:
            dot.game_dots = self.dots

    def load_images(self):
        try:
            def create_shape_surface(shape_type, color, size):
                surface = pygame.Surface((size, size), pygame.SRCALPHA)
                
                if shape_type == 'scissors':
                    # Draw scissors shape (X)
                    pygame.draw.line(surface, color, (3, 3), (size-3, size-3), 2)
                    pygame.draw.line(surface, color, (3, size-3), (size-3, 3), 2)
                
                elif shape_type == 'paper':
                    # Draw paper shape (square)
                    pygame.draw.rect(surface, color, (3, 3, size-6, size-6), 2)
                
                elif shape_type == 'rock':
                    # Draw rock shape (circle)
                    pygame.draw.circle(surface, color, (size//2, size//2), size//2-3, 2)
                
                return surface

            # Make shapes slightly larger than dot radius
            image_size = int(DOT_RADIUS * 2)
            
            # Create shape surfaces
            Game.scissors_img = create_shape_surface('scissors', RED, image_size)
            Game.paper_img = create_shape_surface('paper', GREEN, image_size)
            Game.rock_img = create_shape_surface('rock', BLUE, image_size)
            
        except Exception as e:
            print(f"Error creating shapes: {e}")
            # Fallback to colored circles
            Game.scissors_img = self.create_fallback_surface(RED)
            Game.paper_img = self.create_fallback_surface(GREEN)
            Game.rock_img = self.create_fallback_surface(BLUE)

    def create_fallback_surface(self, color):
        size = int(DOT_RADIUS * 2)
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (size//2, size//2), size//2)
        return surface

    def initialize_dots(self):
        for group in ['A', 'B', 'C']:
            for _ in range(INITIAL_DOTS_PER_GROUP):
                x = random.randint(DOT_RADIUS, WINDOW_WIDTH - DOT_RADIUS)
                y = random.randint(DOT_RADIUS, WINDOW_HEIGHT - DOT_RADIUS)
                self.dots.append(Dot(x, y, group))

    def spawn_bonus_disks(self, count=40):
        for _ in range(count):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(0, self.circle_radius)
            x = self.circle_center[0] + distance * math.cos(angle)
            y = self.circle_center[1] + distance * math.sin(angle)
            self.bonus_disks.append(BonusDisk(x, y))

    def handle_bonus_collisions(self):
        for dot in self.dots:
            for bonus in self.bonus_disks[:]:
                if math.sqrt((dot.x - bonus.x)**2 + (dot.y - bonus.y)**2) < EATING_DISTANCE:
                    dot.apply_bonus()
                    new_dot = Dot(dot.x + random.uniform(-10, 10), dot.y + random.uniform(-10, 10), dot.group)
                    new_dot.game_dots = self.dots
                    self.dots.append(new_dot)
                    self.bonus_disks.remove(bonus)

    def update_targets(self):
        for dot in self.dots:
            closest_prey = None
            closest_predator = None
            min_prey_dist = float('inf')
            min_predator_dist = float('inf')
            
            # Increase prey attraction and reduce predator fear
            PREY_WEIGHT = 1.5      # Increased from 1.0 to make prey more attractive
            PREDATOR_WEIGHT = 0.7  # Decreased from 1.0 to make predators less scary
            
            for other in self.dots:
                if other == dot:
                    continue
                    
                dx = other.x - dot.x
                dy = other.y - dot.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Define prey and predator relationships
                is_prey = (
                    (dot.group == 'A' and other.group == 'B') or
                    (dot.group == 'B' and other.group == 'C') or
                    (dot.group == 'C' and other.group == 'A')
                )
                is_predator = (
                    (dot.group == 'A' and other.group == 'C') or
                    (dot.group == 'B' and other.group == 'A') or
                    (dot.group == 'C' and other.group == 'B')
                )
                
                # Prioritize closer prey
                if is_prey and distance < CHASE_THRESHOLD:
                    weight = PREY_WEIGHT * (1 - distance/CHASE_THRESHOLD)  # Stronger attraction to closer prey
                    if distance < min_prey_dist:
                        min_prey_dist = distance
                        closest_prey = other
                
                # Be less afraid of predators
                elif is_predator and distance < FLEE_THRESHOLD:
                    weight = PREDATOR_WEIGHT * (1 - distance/FLEE_THRESHOLD)  # Weaker repulsion from predators
                    if distance < min_predator_dist:
                        min_predator_dist = distance
                        closest_predator = other

            # Adjust target selection
            if closest_prey and (not closest_predator or min_prey_dist < min_predator_dist * 1.5):
                # More likely to chase prey even when predator is nearby
                dot.target = closest_prey
                dot.fleeing = False
            elif closest_predator:
                dot.target = closest_predator
                dot.fleeing = True
            else:
                dot.target = None
                dot.fleeing = False
                
                # Random movement when no targets
                if random.random() < 0.02:  # 2% chance each frame
                    angle = random.uniform(0, 2 * math.pi)
                    dot.momentum_x = math.cos(angle) * GLOBAL_MAX_SPEED * 0.5
                    dot.momentum_y = math.sin(angle) * GLOBAL_MAX_SPEED * 0.5

    def move_towards_target(self, dot):
        if dot.target:
            dx = dot.target.x - dot.x
            dy = dot.target.y - dot.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                # Normalize direction
                dx /= distance
                dy /= distance
                
                # Apply force based on whether fleeing or chasing
                if dot.fleeing:
                    force = GLOBAL_MIN_SPEED + (GLOBAL_MAX_SPEED - GLOBAL_MIN_SPEED) * 0.7  # Slower when fleeing
                    dx = -dx  # Reverse direction
                    dy = -dy
                else:
                    force = GLOBAL_MIN_SPEED + (GLOBAL_MAX_SPEED - GLOBAL_MIN_SPEED)  # Full speed when chasing
                
                # Add some randomness to movement
                dx += random.uniform(-0.2, 0.2)
                dy += random.uniform(-0.2, 0.2)
                
                # Update momentum with more aggressive acceleration
                dot.momentum_x = dot.momentum_x * 0.95 + dx * force * 0.2
                dot.momentum_y = dot.momentum_y * 0.95 + dy * force * 0.2
        
        # Apply momentum
        dot.x += dot.momentum_x
        dot.y += dot.momentum_y

    def handle_collisions(self):
        i = 0
        collision_occurred = False
        while i < len(self.dots):
            dot1 = self.dots[i]
            j = i + 1
            while j < len(self.dots):
                dot2 = self.dots[j]
                if dot1.distance_to(dot2) < EATING_DISTANCE:
                    if dot1.can_eat(dot2):
                        dot2.group = dot1.group
                        collision_occurred = True
                    elif dot2.can_eat(dot1):
                        dot1.group = dot2.group
                        collision_occurred = True
                j += 1
            i += 1
        return collision_occurred

    def check_winner(self):
        groups = {'A': 0, 'B': 0, 'C': 0}
        for dot in self.dots:
            groups[dot.group] += 1
        
        for group, count in groups.items():
            if count == len(self.dots):
                if not self.winner:
                    self.winner = group
                    self.winner_time = pygame.time.get_ticks()
                return True
        return False

    def display_winner(self, group):
        def draw_large_shape(shape_type, color, center_pos, size):
            surface = pygame.Surface((size, size), pygame.SRCALPHA)
            
            if shape_type == 'A':  # Scissors
                # Draw large X
                thickness = 6
                pygame.draw.line(surface, color, (size//4, size//4), 
                               (size*3//4, size*3//4), thickness)
                pygame.draw.line(surface, color, (size//4, size*3//4), 
                               (size*3//4, size//4), thickness)
            
            elif shape_type == 'B':  # Paper
                # Draw large square
                thickness = 6
                rect = pygame.Rect(size//4, size//4, size//2, size//2)
                pygame.draw.rect(surface, color, rect, thickness)
            
            elif shape_type == 'C':  # Rock
                # Draw large circle
                thickness = 6
                pygame.draw.circle(surface, color, (size//2, size//2), 
                                 size//3, thickness)
            
            return surface

        if group in ['A', 'B', 'C']:
            # Get the color based on group
            color = {
                'A': RED,    # Scissors
                'B': GREEN,  # Paper
                'C': BLUE    # Rock
            }[group]
            
            # Draw large shape
            shape_surface = draw_large_shape(group, color, 
                                          (WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40), 80)
            shape_rect = shape_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40))
            self.screen.blit(shape_surface, shape_rect)
            
            # Draw "WINS!" text below the shape
            wins_text = "WINS!"
            wins_surface = FONT_LARGE.render(wins_text, True, YELLOW)
            wins_rect = wins_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 40))
            self.screen.blit(wins_surface, wins_rect)
        else:
            # For "No one wins" case
            text_surface = FONT_LARGE.render("DRAW!", True, YELLOW)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 - 40))
            self.screen.blit(text_surface, text_rect)
        
        # Create countdown text with softer color
        time_left = (RESTART_DELAY - (pygame.time.get_ticks() - self.winner_time)) // 1000
        if time_left < 0:
            time_left = 0
        countdown_text = f"Restarting in {time_left}..."
        countdown_surface = FONT_MEDIUM.render(countdown_text, True, SOFT_WHITE)
        countdown_rect = countdown_surface.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2 + 100))
        self.screen.blit(countdown_surface, countdown_rect)

    def draw_status_table(self):
        # Count current populations
        populations = {'A': 0, 'B': 0, 'C': 0}
        for dot in self.dots:
            populations[dot.group] += 1

        prey_groups = {
            'A': 'B',
            'B': 'C',
            'C': 'A'
        }

        # Draw table background
        table_width = 300
        table_height = 100
        table_x = 10
        table_y = 10
        pygame.draw.rect(self.screen, WHITE, (table_x, table_y, table_width, table_height))
        pygame.draw.rect(self.screen, BLACK, (table_x, table_y, table_width, table_height), 2)

        # Draw table headers
        y_offset = table_y + 10
        headers = ['Group', 'Can Eat', 'Count']
        for i, header in enumerate(headers):
            text = self.font.render(header, True, BLACK)
            self.screen.blit(text, (table_x + 10 + i * 100, y_offset))

        # Draw horizontal line under headers
        pygame.draw.line(self.screen, BLACK, (table_x, y_offset + 20),
                        (table_x + table_width, y_offset + 20))

        # Get group images
        group_images = {
            'A': Game.scissors_img,
            'B': Game.paper_img,
            'C': Game.rock_img
        }

        # Draw table content
        icon_size = 20  # Size for the shape icons
        for i, group in enumerate(['A', 'B', 'C']):
            y = y_offset + 30 + i * 20
            
            # Group shape (centered in column)
            img = group_images[group]
            img_rect = img.get_rect(center=(table_x + 50, y + icon_size//2))
            self.screen.blit(img, img_rect)
            
            # Can eat (show shape of prey)
            prey_group = prey_groups[group]
            prey_img = group_images[prey_group]
            prey_rect = prey_img.get_rect(center=(table_x + 150, y + icon_size//2))
            self.screen.blit(prey_img, prey_rect)
            
            # Count
            text = self.font.render(str(populations[group]), True, BLACK)
            self.screen.blit(text, (table_x + 210, y))

    def is_inside_circle(self, x, y):
        distance_to_center = math.sqrt((x - self.circle_center[0])**2 + (y - self.circle_center[1])**2)
        return distance_to_center <= self.circle_radius

    def force_towards_circle(self, dot):
        if not self.is_inside_circle(dot.x, dot.y):
            dx = self.circle_center[0] - dot.x
            dy = self.circle_center[1] - dot.y
            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                dot.x += (dx/distance) * OUTSIDE_CIRCLE_FORCE
                dot.y += (dy/distance) * OUTSIDE_CIRCLE_FORCE

    def run(self):
        running = True
        initial_radius = self.circle_radius
        last_collision_time = pygame.time.get_ticks()

        while running:
            current_time = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Check for game restart
            if self.winner and current_time - self.winner_time >= RESTART_DELAY:
                self.reset_game()

            self.circle_radius -= CIRCLE_SHRINK_SPEED
            if self.circle_radius < 0:
                self.circle_radius = 0

            current_ratio = self.circle_radius / initial_radius

            # Check for bonus disk spawning at different thresholds
            for threshold in [0.8, 0.7, 0.6, 0.4]:
                if not self.bonus_spawned[threshold] and current_ratio <= threshold:
                    self.spawn_bonus_disks(10 if threshold == 0.7 else 8)
                    self.bonus_spawned[threshold] = True

            if not self.winner:
                self.update_targets()
                for dot in self.dots:
                    dot.update_bonus()
                    self.move_towards_target(dot)
                    self.force_towards_circle(dot)

                if self.handle_collisions():
                    last_collision_time = current_time
                self.handle_bonus_collisions()

            # Drawing
            # Create a gradient background
            for y in range(WINDOW_HEIGHT):
                progress = y / WINDOW_HEIGHT
                color = [
                    int(DEEP_BLUE[0] * (1 - progress) + BLACK[0] * progress),
                    int(DEEP_BLUE[1] * (1 - progress) + BLACK[1] * progress),
                    int(DEEP_BLUE[2] * (1 - progress) + BLACK[2] * progress)
                ]
                pygame.draw.line(self.screen, color, (0, y), (WINDOW_WIDTH, y))
            
            # Draw play zone circle with a glowing effect
            if self.circle_radius > 0:
                # Draw outer glow
                for i in range(3):
                    glow_radius = self.circle_radius + (3 - i)
                    glow_color = (
                        CIRCLE_COLOR[0] // (i + 2),
                        CIRCLE_COLOR[1] // (i + 2),
                        CIRCLE_COLOR[2] // (i + 2)
                    )
                    pygame.draw.circle(self.screen, glow_color,
                                    (int(self.circle_center[0]), int(self.circle_center[1])),
                                    int(glow_radius), 1)
                # Draw main circle
                pygame.draw.circle(self.screen, CIRCLE_COLOR,
                                (int(self.circle_center[0]), int(self.circle_center[1])),
                                int(self.circle_radius), 2)

            # Draw bonus disks with subtle glow
            for bonus in self.bonus_disks:
                # Draw glow
                pygame.draw.circle(self.screen, (PURPLE[0]//2, PURPLE[1]//2, PURPLE[2]//2),
                                (int(bonus.x), int(bonus.y)),
                                int(bonus.radius + 2))
                # Draw main disk
                pygame.draw.circle(self.screen, PURPLE,
                                (int(bonus.x), int(bonus.y)),
                                int(bonus.radius))
            
            # Draw dots
            for dot in self.dots:
                if dot.momentum_x != 0 or dot.momentum_y != 0:
                    angle = math.degrees(math.atan2(-dot.momentum_y, dot.momentum_x))
                    dot.last_angle = angle
                else:
                    angle = dot.last_angle

                img = dot.get_image()
                rotated_img = pygame.transform.rotate(img, angle)
                img_rect = rotated_img.get_rect(center=(int(dot.x), int(dot.y)))
                self.screen.blit(rotated_img, img_rect)

            # Draw status table
            self.draw_status_table()

            # Check for winner
            if self.check_winner() or len(self.dots) == 0:
                if len(self.dots) > 0:
                    self.display_winner(self.winner)
                else:
                    self.display_winner("No one")

            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
