import pygame
import random
import math
from pygame import Vector2
from constants import *
from pathfinding import get_path, invalidate_paths_to
import sprites

class ResourceNode:
    """Clase para representar minas de oro en el mapa."""
    def __init__(self, x, y, amount=500, resource_type='gold'):
        self.pos = Vector2(x, y)
        self.amount = amount
        self.max_amount = amount
        self.z_order = 0
        self.resource_type = resource_type

    def draw(self, screen, camera):
        if self.amount <= 0:
            return
        screen_pos = camera.apply(self.pos)
        if sprites.resource_sprites.get('gold'):
            sprite = sprites.resource_sprites['gold']
            rect = sprite.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
            screen.blit(sprite, rect)
            bar_width = 30
            bar_height = 4
            bar_x = int(screen_pos.x) - bar_width // 2
            bar_y = int(screen_pos.y) - 25
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (255, 215, 0),
                           (bar_x, bar_y, int(bar_width * (self.amount / self.max_amount)), bar_height))
        else:
            size = int(10 + (self.amount / self.max_amount) * 10)
            color = (255, 215, 0)
            pygame.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), size)
            font = pygame.font.SysFont("Arial", 12)
            txt = font.render(f"{int(self.amount)}", True, UI_COLOR)
            screen.blit(txt, (int(screen_pos.x) - txt.get_width()//2, int(screen_pos.y) - 25))

class Tree:
    """Árbol con madera para talar."""
    def __init__(self, x, y):
        self.pos = Vector2(x, y)
        self.z_order = y
        self.wood_amount = random.randint(80, 150)
        self.max_wood = self.wood_amount
        self.resource_type = 'wood'
        self.amount = self.wood_amount
        self.sprite = random.choice(sprites.environment_sprites['trees']) if sprites.environment_sprites.get('trees') else None

    def draw(self, screen, camera):
        screen_pos = camera.apply(self.pos)
        if self.sprite:
            rect = self.sprite.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
            screen.blit(self.sprite, rect)
        else:
            pygame.draw.rect(screen, (101, 67, 33),
                            (int(screen_pos.x) - 3, int(screen_pos.y) - 5, 6, 15))
            pygame.draw.circle(screen, (34, 139, 34), (int(screen_pos.x), int(screen_pos.y) - 8), 10)
        if self.wood_amount < self.max_wood:
            bar_width = 30
            bar_height = 4
            bar_x = int(screen_pos.x) - bar_width // 2
            bar_y = int(screen_pos.y) - 30
            pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(screen, (139, 69, 19),
                           (bar_x, bar_y, int(bar_width * (self.wood_amount / self.max_wood)), bar_height))

def draw_unit_shape(screen, pos, shape_type, color, size=12, selected=False):
    """Dibuja diferentes formas según el tipo de unidad (fallback)."""
    x, y = int(pos.x), int(pos.y)
    
    if shape_type == 'circle':
        pygame.draw.circle(screen, color, (x, y), size)
        if selected:
            pygame.draw.circle(screen, SELECT_COLOR, (x, y), size + 3, 2)
    elif shape_type == 'square':
        rect = pygame.Rect(x - size, y - size, size * 2, size * 2)
        pygame.draw.rect(screen, color, rect)
        if selected:
            pygame.draw.rect(screen, SELECT_COLOR, rect.inflate(6, 6), 2)
    elif shape_type == 'triangle':
        points = [(x, y - size), (x - size, y + size), (x + size, y + size)]
        pygame.draw.polygon(screen, color, points)
        if selected:
            points_outline = [(x, y - size - 3), (x - size - 3, y + size + 3), (x + size + 3, y + size + 3)]
            pygame.draw.polygon(screen, SELECT_COLOR, points_outline, 2)
    elif shape_type == 'diamond':
        points = [(x, y - size), (x + size, y), (x, y + size), (x - size, y)]
        pygame.draw.polygon(screen, color, points)
        if selected:
            points_outline = [(x, y - size - 3), (x + size + 3, y), (x, y + size + 3), (x - size - 3, y)]
            pygame.draw.polygon(screen, SELECT_COLOR, points_outline, 2)

class Unit:
    def __init__(self, x, y, is_enemy=False):
        self.pos = Vector2(x, y)
        self.path = []
        self.speed = UNIT_SPEED
        self.selected = False
        self.hp = 100
        self.max_hp = 100
        self.attack_damage = 10
        self.attack_range = 50
        self.attack_cooldown = 60
        self.current_cooldown = 0
        self.target_entity = None
        self._last_target_tile = None
        self.is_enemy = is_enemy
        self.z_order = self.pos.y
        self.formation_offset = Vector2(0, 0)
        self.auto_defend = True
        self.attacker = None

    def _separation(self, nearby_units):
        steer = Vector2(0, 0)
        count = 0
        for other in nearby_units:
            if other is self or getattr(other, "hp", 0) <= 0:
                continue
            diff = self.pos - other.pos
            dist_sq = diff.length_squared()
            if dist_sq == 0:
                diff = Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
                dist_sq = 1.0
            if dist_sq <= SEPARATION_RADIUS * SEPARATION_RADIUS:
                dist = math.sqrt(dist_sq)
                force = (SEPARATION_RADIUS - dist) / SEPARATION_RADIUS
                steer += diff.normalize() * force * 2.0
                count += 1
        if count > 0:
            steer /= count
        return steer

    def update(self, obstacles, resources=None, base=None, all_units=None, trees=None):
        if self.hp <= 0:
            return
        self.z_order = self.pos.y

        if self.auto_defend and self.attacker and not self.target_entity:
            if getattr(self.attacker, "hp", 0) > 0:
                self.target_entity = self.attacker

        if self.target_entity and getattr(self.target_entity, "hp", 0) > 0:
            dist = self.pos.distance_to(self.target_entity.pos)
            if dist <= self.attack_range:
                self.path = []
                self.attack()
            elif not self.path:
                self.path = get_path(self.pos, self.target_entity.pos, obstacles)
        elif self.target_entity:
            self.target_entity = None

        if self.path:
            target_node = self.path[0]
            desired = target_node - self.pos
            if desired.length_squared() != 0:
                sep = self._separation(all_units) if all_units else Vector2(0, 0)
                desired_normalized = desired.normalize()
                combined = desired_normalized + sep * SEPARATION_WEIGHT
                move_dir = combined.normalize() if combined.length_squared() > 0 else desired_normalized
                if self.pos.distance_to(target_node) > self.speed:
                    self.pos += move_dir * self.speed
                else:
                    self.pos = Vector2(target_node)
                    self.path.pop(0)

        if self.current_cooldown > 0:
            self.current_cooldown -= 1

    def attack(self):
        if self.current_cooldown <= 0 and self.target_entity:
            self.target_entity.take_damage(self.attack_damage, attacker=self)
            self.current_cooldown = self.attack_cooldown

    def take_damage(self, amount, attacker=None):
        self.hp = max(0, self.hp - amount)
        if attacker and self.auto_defend:
            self.attacker = attacker

    def draw(self, screen, camera):
        if self.hp <= 0: 
            return
        screen_pos = camera.apply(self.pos)
        class_name = self.__class__.__name__
        sprite_key = 'EnemyUnit' if self.is_enemy else class_name
        sprite = sprites.unit_sprites.get(sprite_key)
        if sprite:
            if self.selected:
                pygame.draw.circle(screen, SELECT_COLOR, (int(screen_pos.x), int(screen_pos.y)), 18, 2)
            rect = sprite.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
            screen.blit(sprite, rect)
        else:
            shape = UNIT_SHAPES.get(class_name, 'circle')
            color = ENEMY_COLOR if self.is_enemy else PLAYER_COLOR
            if self.selected:
                color = tuple(min(255, c + 50) for c in color)
            draw_unit_shape(screen, screen_pos, shape, color, 12, self.selected)
        self._draw_hp_bar(screen, screen_pos)

    def _draw_hp_bar(self, screen, screen_pos):
        bar_w = 20
        bar_rect = pygame.Rect(screen_pos.x - bar_w/2, screen_pos.y - 20, bar_w, 4)
        pygame.draw.rect(screen, (255, 0, 0), bar_rect)
        pygame.draw.rect(screen, (0, 255, 0), (bar_rect.x, bar_rect.y, bar_w * (self.hp/self.max_hp), 4))

class Villager(Unit):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y, is_enemy)
        self.speed = VILLAGER_SPEED
        self.carry = 0.0
        self.carry_capacity = 25.0
        self.carry_type = None
        self.state = "idle"
        self.target_resource = None
        self._just_deposited = {'gold': 0, 'wood': 0}
        self.auto_defend = False
        self.building_target = None  # ConstructionSite al que está asignado

    def update(self, obstacles, resources=None, base=None, all_units=None, trees=None):
        if self.hp <= 0:
            return
        self.z_order = self.pos.y

        # Prioridad: construcción
        if self.building_target:
            if not self.building_target.under_construction or self.building_target.completed:
                self.building_target = None
                self.state = "idle"
            else:
                # Moverse hacia la obra
                if self.pos.distance_to(self.building_target.pos) <= TILE_SIZE:
                    self.path = []
                else:
                    if not self.path or self.path[-1] != self.building_target.pos:
                        self.path = get_path(self.pos, self.building_target.pos, obstacles)
                # El progreso lo maneja la obra, no hacemos más aquí
                # Pero seguimos con el movimiento
                if self.path:
                    target_node = self.path[0]
                    desired = target_node - self.pos
                    if desired.length_squared() != 0:
                        sep = self._separation(all_units) if all_units else Vector2(0, 0)
                        desired_normalized = desired.normalize()
                        combined = desired_normalized + sep * SEPARATION_WEIGHT
                        move_dir = combined.normalize() if combined.length_squared() > 0 else desired_normalized
                        if self.pos.distance_to(target_node) > self.speed:
                            self.pos += move_dir * self.speed
                        else:
                            self.pos = Vector2(target_node)
                            self.path.pop(0)
                return  # No hace otras cosas mientras construye

        # Lógica de recolección (igual que antes)
        if self.state == "idle":
            available_resources = [r for r in resources if r.amount > 0]
            if available_resources:
                self.target_resource = min(available_resources, key=lambda r: self.pos.distance_to(r.pos))
                self.state = "moving_to_resource"
                self.path = get_path(self.pos, self.target_resource.pos, obstacles)
            else:
                available_trees = [t for t in trees if t.wood_amount > 0]
                if available_trees:
                    self.target_resource = min(available_trees, key=lambda t: self.pos.distance_to(t.pos))
                    self.state = "moving_to_resource"
                    self.path = get_path(self.pos, self.target_resource.pos, obstacles)

        elif self.state == "moving_to_resource" and self.target_resource:
            if self.pos.distance_to(self.target_resource.pos) <= TILE_SIZE:
                self.state = "gathering"
                self.carry_type = self.target_resource.resource_type
                self.path = []
            elif not self.path:
                self.path = get_path(self.pos, self.target_resource.pos, obstacles)

        elif self.state == "gathering":
            if self.carry >= self.carry_capacity:
                self.state = "returning"
                if base: 
                    self.path = get_path(self.pos, base.pos, obstacles)
            elif not self.target_resource or (hasattr(self.target_resource, 'amount') and self.target_resource.amount <= 0) or (hasattr(self.target_resource, 'wood_amount') and self.target_resource.wood_amount <= 0):
                self.state = "returning"
                if base: 
                    self.path = get_path(self.pos, base.pos, obstacles)
            elif self.target_resource:
                if hasattr(self.target_resource, 'amount'):
                    amt = min(GATHER_RATE, self.target_resource.amount, self.carry_capacity - self.carry)
                    self.target_resource.amount -= amt
                    self.carry += amt
                elif hasattr(self.target_resource, 'wood_amount'):
                    amt = min(GATHER_RATE, self.target_resource.wood_amount, self.carry_capacity - self.carry)
                    self.target_resource.wood_amount -= amt
                    self.target_resource.amount = self.target_resource.wood_amount
                    self.carry += amt

        elif self.state == "returning" and base:
            if self.pos.distance_to(base.pos) <= TILE_SIZE * 1.5:
                if self.carry_type:
                    self._just_deposited[self.carry_type] = self.carry
                self.carry = 0.0
                self.carry_type = None
                self.state = "idle"
                self.path = []
            elif not self.path:
                self.path = get_path(self.pos, base.pos, obstacles)

        # Movimiento común
        if self.path:
            target_node = self.path[0]
            desired = target_node - self.pos
            if desired.length_squared() != 0:
                sep = self._separation(all_units) if all_units else Vector2(0, 0)
                combined = desired.normalize() + sep * SEPARATION_WEIGHT
                move_dir = combined.normalize() if combined.length_squared() > 0 else desired.normalize()
                if self.pos.distance_to(target_node) > self.speed:
                    self.pos += move_dir * self.speed
                else:
                    self.pos = Vector2(target_node)
                    self.path.pop(0)

    def take_deposit(self):
        deposits = self._just_deposited.copy()
        self._just_deposited = {'gold': 0, 'wood': 0}
        return deposits

    def draw(self, screen, camera):
        if self.hp <= 0:
            return
        screen_pos = camera.apply(self.pos)
        sprite_key = 'Villager' if not self.is_enemy else 'EnemyUnit'
        sprite = sprites.unit_sprites.get(sprite_key)
        if sprite:
            if self.selected:
                pygame.draw.circle(screen, SELECT_COLOR, (int(screen_pos.x), int(screen_pos.y)), 18, 2)
            rect = sprite.get_rect(center=(int(screen_pos.x), int(screen_pos.y)))
            screen.blit(sprite, rect)
        else:
            color = VILLAGER_COLOR if not self.is_enemy else (200, 150, 100)
            if self.selected:
                color = tuple(min(255, c + 50) for c in color)
            draw_unit_shape(screen, screen_pos, 'circle', color, 12, self.selected)
        self._draw_hp_bar(screen, screen_pos)
        if self.carry > 0:
            font = pygame.font.SysFont("Arial", 12)
            carry_color = (255, 215, 0) if self.carry_type == 'gold' else (139, 69, 19)
            txt = font.render(str(int(self.carry)), True, carry_color)
            screen.blit(txt, (screen_pos.x - txt.get_width()//2, screen_pos.y - 32))

class Swordsman(Unit):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y, is_enemy)
        self.hp = 140
        self.max_hp = 140
        self.attack_damage = 18
        self.speed = UNIT_SPEED

class Archer(Unit):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y, is_enemy)
        self.hp = 90
        self.max_hp = 90
        self.attack_range = 120
        self.speed = ARCHER_SPEED

class Building:
    def __init__(self, x, y):
        # x, y son coordenadas del centro
        self.rect = pygame.Rect(x - TILE_SIZE*1.5, y - TILE_SIZE*1.5, TILE_SIZE*3, TILE_SIZE*3)
        self.pos = Vector2(self.rect.center)
        self.selected = False
        self.hp = 1000
        self.max_hp = 1000
        self.z_order = self.pos.y
        self.under_construction = False
        self.construction_progress = 0
        self.construction_time_max = 0
        self.is_enemy = False

    def take_damage(self, amount, attacker=None):
        self.hp = max(0, self.hp - amount)

    def update_construction(self):
        if self.under_construction:
            self.construction_progress += 1
            if self.construction_progress >= self.construction_time_max:
                self.under_construction = False
                self.construction_progress = 0

    def draw(self, screen, camera):
        if self.hp <= 0: 
            return
        screen_rect = self.rect.copy()
        screen_rect.topleft = camera.apply(Vector2(self.rect.topleft))
        
        class_name = self.__class__.__name__
        if self.is_enemy and class_name == 'PlayerBase':
            class_name = 'EnemyBase'
        elif self.is_enemy and class_name == 'Barracks':
            class_name = 'EnemyBarracks'
        
        sprite = sprites.building_sprites.get(class_name)
        if sprite:
            img = pygame.transform.scale(sprite, (self.rect.width, self.rect.height))
            screen.blit(img, screen_rect.topleft)
        else:
            color = (100, 100, 100) if self.under_construction else BASE_COLOR
            pygame.draw.rect(screen, color, screen_rect)
        
        if self.selected: 
            pygame.draw.rect(screen, SELECT_COLOR, screen_rect, 3)
        
        bar_rect = pygame.Rect(screen_rect.x, screen_rect.y - 15, self.rect.width, 8)
        pygame.draw.rect(screen, (255,0,0), bar_rect)
        pygame.draw.rect(screen, (0,255,0), (bar_rect.x, bar_rect.y, bar_rect.width * (self.hp/self.max_hp), 8))
        
        if self.under_construction:
            progress = self.construction_progress / self.construction_time_max
            construction_bar = pygame.Rect(screen_rect.x, screen_rect.y - 25, self.rect.width, 5)
            pygame.draw.rect(screen, (50, 50, 50), construction_bar)
            pygame.draw.rect(screen, (255, 200, 0), 
                           (construction_bar.x, construction_bar.y, int(construction_bar.width * progress), 5))

class PlayerBase(Building):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y)
        self.hp = 2000
        self.max_hp = 2000
        self.villager_cooldown = 0
        self.villager_cooldown_max = UNIT_COSTS['villager']['time']
        self.is_enemy = is_enemy
    
    def can_train_villager(self):
        return self.villager_cooldown <= 0 and not self.under_construction
    
    def start_train_villager(self):
        self.villager_cooldown = self.villager_cooldown_max
    
    def update(self):
        if self.villager_cooldown > 0:
            self.villager_cooldown -= 1
        self.update_construction()
    
    def draw(self, screen, camera):
        super().draw(screen, camera)
        if self.villager_cooldown > 0 and not self.is_enemy:
            screen_rect = self.rect.copy()
            screen_rect.topleft = camera.apply(Vector2(self.rect.topleft))
            cooldown_rect = pygame.Rect(screen_rect.x, screen_rect.y - 35, self.rect.width, 5)
            progress = 1 - (self.villager_cooldown / self.villager_cooldown_max)
            pygame.draw.rect(screen, (50, 50, 50), cooldown_rect)
            pygame.draw.rect(screen, (200, 200, 100), 
                           (cooldown_rect.x, cooldown_rect.y, int(cooldown_rect.width * progress), 5))

class Barracks(Building):
    def __init__(self, x, y, is_enemy=False):
        super().__init__(x, y)
        self.train_time = {
            "swordsman": UNIT_COSTS['swordsman']['time'],
            "archer": UNIT_COSTS['archer']['time'],
            "villager": UNIT_COSTS['villager']['time']
        }
        self.queue = []
        self._anim_timer = 0
        self.is_enemy = is_enemy

    def train(self, unit_type):
        if unit_type in self.train_time:
            self.queue.append([unit_type, self.train_time[unit_type]])

    def can_train(self):
        return len(self.queue) < 5 and not self.under_construction

    def tick_queue(self):
        if not self.queue or self.under_construction: 
            return None
        self.queue[0][1] -= 1
        if self.queue[0][1] <= 0:
            self._anim_timer = 30
            return self.queue.pop(0)[0]
        return None
    
    def update(self):
        self.update_construction()
    
    def draw(self, screen, camera):
        super().draw(screen, camera)
        if self.queue and not self.under_construction:
            screen_rect = self.rect.copy()
            screen_rect.topleft = camera.apply(Vector2(self.rect.topleft))
            font = pygame.font.SysFont("Arial", 16)
            txt = font.render(f"{len(self.queue)}", True, UI_COLOR)
            screen.blit(txt, (screen_rect.centerx - txt.get_width()//2, screen_rect.centery - txt.get_height()//2 + 20))

class EnemyBase(PlayerBase):
    def __init__(self, x, y):
        super().__init__(x, y, is_enemy=True)
        self.gold = 1000
        self.wood = 500
        self.warmup_time = 10 * FPS
        
    def update(self):
        super().update()
        self.gold += 0.5
        self.wood += 0.3
        if self.warmup_time > 0:
            self.warmup_time -= 1
    
    def is_ready_to_train(self):
        return self.warmup_time <= 0
    
    def add_resources(self, gold, wood):
        self.gold += gold
        self.wood += wood

class ConstructionSite(Building):
    """Representa un edificio en construcción."""
    def __init__(self, x, y, building_type):
        super().__init__(x, y)
        self.building_type = building_type  # 'town_center' o 'barracks'
        self.under_construction = True
        self.construction_progress = 0
        self.construction_time_max = BUILDING_COSTS[building_type]['time']
        self.assigned_villager = None
        self.completed = False
        # No tiene vida hasta que se complete
        self.hp = 1  # para que no muera fácilmente
        self.max_hp = 1

    def update(self):
        if self.assigned_villager and self.assigned_villager.hp > 0:
            # Si el aldeano está en el sitio, avanza la construcción
            if self.pos.distance_to(self.assigned_villager.pos) <= TILE_SIZE:
                self.construction_progress += 1
                if self.construction_progress >= self.construction_time_max:
                    self.completed = True
                    self.under_construction = False
        # Si no hay aldeano o murió, la construcción se detiene (no avanzamos)

    def draw(self, screen, camera):
        # Dibujar el esqueleto del edificio (usamos el mismo sprite pero semitransparente o un placeholder)
        screen_rect = self.rect.copy()
        screen_rect.topleft = camera.apply(Vector2(self.rect.topleft))
        
        # Placeholder: rectángulo gris
        color = (100, 100, 100)
        pygame.draw.rect(screen, color, screen_rect)
        pygame.draw.rect(screen, (150,150,150), screen_rect, 2)
        
        # Barra de progreso
        progress = self.construction_progress / self.construction_time_max
        bar_width = self.rect.width
        bar_height = 8
        bar_x = screen_rect.x
        bar_y = screen_rect.y - 20
        pygame.draw.rect(screen, (50,50,50), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (255,200,0), (bar_x, bar_y, int(bar_width * progress), bar_height))
        
        # Texto "Construyendo"
        font = pygame.font.SysFont("Arial", 14)
        text = font.render("Construyendo", True, (255,255,0))
        screen.blit(text, (screen_rect.centerx - text.get_width()//2, bar_y - 20))