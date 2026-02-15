import pygame
import random
import math
from pygame import Vector2
from constants import *
from camera import Camera
from entities import *
from pathfinding import update_obstacles, tick as pathfinding_tick
import sprites

try:
    pygame.mixer.init()
    _training_complete_sound = None
except:
    _training_complete_sound = None

def _play_training_complete_sound():
    if _training_complete_sound:
        _training_complete_sound.play()

def generate_forests(world_size, coverage=0.7, min_cluster=15, max_cluster=40):
    trees = []
    total_area = world_size * world_size
    target_tree_count = int((total_area * coverage) / 400)
    num_clusters = random.randint(20, 35)
    for _ in range(num_clusters):
        center_x = random.randint(100, world_size - 100)
        center_y = random.randint(100, world_size - 100)
        cluster_size = random.randint(min_cluster, max_cluster)
        for _ in range(cluster_size):
            offset_x = random.randint(-80, 80)
            offset_y = random.randint(-80, 80)
            tree_x = center_x + offset_x
            tree_y = center_y + offset_y
            if 50 < tree_x < world_size - 50 and 50 < tree_y < world_size - 50:
                trees.append(Tree(tree_x, tree_y))
    return trees

def generate_resources(world_size):
    resources = []
    num_gold_nodes = random.randint(8, 12)
    for _ in range(num_gold_nodes):
        x = random.randint(200, world_size - 200)
        y = random.randint(200, world_size - 200)
        amount = random.randint(400, 700)
        resources.append(ResourceNode(x, y, amount, 'gold'))
    return resources

def ensure_clear_path(trees, start_pos, end_pos, path_width=150):
    trees_to_remove = []
    for tree in trees:
        dx = end_pos.x - start_pos.x
        dy = end_pos.y - start_pos.y
        length_sq = dx*dx + dy*dy
        if length_sq == 0:
            continue
        t = max(0, min(1, ((tree.pos.x - start_pos.x) * dx + (tree.pos.y - start_pos.y) * dy) / length_sq))
        projection_x = start_pos.x + t * dx
        projection_y = start_pos.y + t * dy
        distance = math.sqrt((tree.pos.x - projection_x)**2 + (tree.pos.y - projection_y)**2)
        if distance < path_width:
            trees_to_remove.append(tree)
    for tree in trees_to_remove:
        trees.remove(tree)
    return trees

class Minimap:
    def __init__(self, world_size, minimap_size=150):
        self.world_size = world_size
        self.minimap_size = minimap_size
        self.scale = minimap_size / world_size
        self.margin = 10
        self.pos = Vector2(WIDTH - minimap_size - self.margin, HEIGHT - minimap_size - self.margin)
        self.rect = pygame.Rect(self.pos.x, self.pos.y, minimap_size, minimap_size)
        
    def draw(self, screen, camera, units, enemies, resources, player_base, enemy_base, barracks_list, enemy_barracks_list, trees):
        pygame.draw.rect(screen, (50, 50, 50), self.rect)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2)
        base_pos = self._world_to_minimap(player_base.pos)
        pygame.draw.circle(screen, (0, 200, 0), (int(base_pos.x), int(base_pos.y)), 4)
        if enemy_base:
            enemy_base_pos = self._world_to_minimap(enemy_base.pos)
            pygame.draw.circle(screen, (200, 0, 0), (int(enemy_base_pos.x), int(enemy_base_pos.y)), 4)
        for tree in trees:
            if tree.wood_amount > 0:
                tree_pos = self._world_to_minimap(tree.pos)
                pygame.draw.circle(screen, (0, 150, 0), (int(tree_pos.x), int(tree_pos.y)), 1)
        for resource in resources:
            if resource.amount > 0:
                res_pos = self._world_to_minimap(resource.pos)
                pygame.draw.circle(screen, (255, 215, 0), (int(res_pos.x), int(res_pos.y)), 2)
        for barrack in barracks_list:
            b_pos = self._world_to_minimap(barrack.pos)
            pygame.draw.rect(screen, (100, 100, 200), (int(b_pos.x) - 2, int(b_pos.y) - 2, 4, 4))
        for barrack in enemy_barracks_list:
            b_pos = self._world_to_minimap(barrack.pos)
            pygame.draw.rect(screen, (200, 100, 100), (int(b_pos.x) - 2, int(b_pos.y) - 2, 4, 4))
        for unit in units:
            if unit.hp > 0:
                unit_pos = self._world_to_minimap(unit.pos)
                pygame.draw.circle(screen, PLAYER_COLOR, (int(unit_pos.x), int(unit_pos.y)), 1)
        for enemy in enemies:
            if enemy.hp > 0:
                enemy_pos = self._world_to_minimap(enemy.pos)
                pygame.draw.circle(screen, ENEMY_COLOR, (int(enemy_pos.x), int(enemy_pos.y)), 1)
        self._draw_camera_view(screen, camera)
    
    def _world_to_minimap(self, world_pos):
        minimap_x = self.pos.x + (world_pos.x * self.scale)
        minimap_y = self.pos.y + (world_pos.y * self.scale)
        return Vector2(minimap_x, minimap_y)
    
    def _draw_camera_view(self, screen, camera):
        view_x = -camera.offset.x * self.scale
        view_y = -camera.offset.y * self.scale
        view_w = WIDTH * self.scale
        view_h = HEIGHT * self.scale
        view_rect = pygame.Rect(self.pos.x + view_x, self.pos.y + view_y, view_w, view_h)
        pygame.draw.rect(screen, (255, 255, 255), view_rect, 1)
    
    def world_pos_from_minimap_click(self, click_pos):
        if not self.rect.collidepoint(click_pos):
            return None
        rel_x = click_pos[0] - self.pos.x
        rel_y = click_pos[1] - self.pos.y
        world_x = rel_x / self.scale
        world_y = rel_y / self.scale
        return Vector2(world_x, world_y)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.font = pygame.font.SysFont("Arial", 13, bold=True)
        self.enabled = True
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos) and self.enabled
    
    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.color
        if not self.enabled:
            color = tuple(c // 2 for c in color)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2)
        text_surf = self.font.render(self.text, True, (255, 255, 255) if self.enabled else (128, 128, 128))
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
    
    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos) and self.enabled

class HUD:
    def __init__(self):
        self.font_large = pygame.font.SysFont("Arial", 24, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 16)
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.top_panel_height = 50
        self.bottom_panel_height = 180
        self.build_buttons = []
        self.train_buttons = []
        self.formation_buttons = []
        self._create_buttons()
        
    def _create_buttons(self):
        btn_y = HEIGHT - self.bottom_panel_height + 100
        self.build_town_center_btn = Button(20, btn_y, 140, 35, "Centro (400)", (100, 150, 100), (120, 180, 120))
        self.build_barracks_btn = Button(170, btn_y, 140, 35, "Cuartel (150)", (80, 80, 120), (100, 100, 150))
        self.build_buttons = [self.build_town_center_btn, self.build_barracks_btn]
        
        btn_y = HEIGHT - self.bottom_panel_height + 100
        self.train_villager_btn = Button(20, btn_y, 110, 35, "Aldeano (50)", (150, 150, 80), (180, 180, 100))
        self.train_swordsman_btn = Button(140, btn_y, 130, 35, "Espad (200)", (80, 100, 150), (100, 120, 180))
        self.train_archer_btn = Button(280, btn_y, 130, 35, "Arq (150/100)", (80, 150, 100), (100, 180, 120))
        self.train_buttons = [self.train_villager_btn, self.train_swordsman_btn, self.train_archer_btn]
        
        btn_y = HEIGHT - self.bottom_panel_height + 140
        self.form_line_btn = Button(20, btn_y, 80, 30, "Linea", (100, 100, 100), (130, 130, 130))
        self.form_box_btn = Button(110, btn_y, 80, 30, "Caja", (100, 100, 100), (130, 130, 130))
        self.form_column_btn = Button(200, btn_y, 80, 30, "Columna", (100, 100, 100), (130, 130, 130))
        self.form_wedge_btn = Button(290, btn_y, 80, 30, "Cuna", (100, 100, 100), (130, 130, 130))
        self.formation_buttons = [self.form_line_btn, self.form_box_btn, self.form_column_btn, self.form_wedge_btn]
        
    def update(self, mouse_pos, player_base=None, gold=0, wood=0):
        for btn in self.build_buttons + self.train_buttons + self.formation_buttons:
            btn.update(mouse_pos)
        if player_base and isinstance(player_base, PlayerBase):
            self.train_villager_btn.enabled = player_base.can_train_villager() and gold >= UNIT_COSTS['villager']['gold']
        self.build_town_center_btn.enabled = gold >= BUILDING_COSTS['town_center']['gold']
        self.build_barracks_btn.enabled = gold >= BUILDING_COSTS['barracks']['gold']
        self.train_swordsman_btn.enabled = gold >= UNIT_COSTS['swordsman']['gold']
        self.train_archer_btn.enabled = gold >= UNIT_COSTS['archer']['gold'] and wood >= UNIT_COSTS['archer']['wood']
    
    def draw_top_panel(self, screen, gold, wood, units, enemies, resources):
        panel_surface = pygame.Surface((WIDTH, self.top_panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((40, 40, 40))
        screen.blit(panel_surface, (0, 0))
        pygame.draw.rect(screen, (100, 100, 100), (0, 0, WIDTH, self.top_panel_height), 2)
        gold_text = f"Oro: {int(gold)}"
        gold_surface = self.font_large.render(gold_text, True, (255, 215, 0))
        screen.blit(gold_surface, (20, 12))
        wood_text = f"Madera: {int(wood)}"
        wood_surface = self.font_medium.render(wood_text, True, (139, 69, 19))
        screen.blit(wood_surface, (180, 15))
        units_alive = len([u for u in units if u.hp > 0])
        pop_text = f"Poblacion: {units_alive}"
        pop_surface = self.font_medium.render(pop_text, True, (255, 255, 255))
        screen.blit(pop_surface, (380, 15))
        enemies_alive = len([e for e in enemies if e.hp > 0])
        enemy_text = f"Enemigos: {enemies_alive}"
        enemy_surface = self.font_medium.render(enemy_text, True, (255, 100, 100))
        screen.blit(enemy_surface, (550, 15))
        total_resources = sum([r.amount for r in resources])
        res_text = f"Recursos: {int(total_resources)}"
        res_surface = self.font_medium.render(res_text, True, (150, 200, 255))
        screen.blit(res_surface, (750, 15))
        
    def draw_bottom_panel(self, screen, selected_units, selected_buildings):
        if not selected_units and not selected_buildings:
            return
        panel_surface = pygame.Surface((WIDTH, self.bottom_panel_height))
        panel_surface.set_alpha(200)
        panel_surface.fill((40, 40, 40))
        screen.blit(panel_surface, (0, HEIGHT - self.bottom_panel_height))
        pygame.draw.rect(screen, (100, 100, 100), (0, HEIGHT - self.bottom_panel_height, WIDTH, self.bottom_panel_height), 2)
        y_offset = HEIGHT - self.bottom_panel_height + 10
        if selected_units:
            self._draw_unit_info(screen, selected_units, y_offset)
            villagers = [u for u in selected_units if isinstance(u, Villager)]
            if villagers:
                for btn in self.build_buttons:
                    btn.draw(screen)
            if len(selected_units) > 1:
                for btn in self.formation_buttons:
                    btn.draw(screen)
        elif selected_buildings:
            self._draw_building_info(screen, selected_buildings[0], y_offset)
            if isinstance(selected_buildings[0], PlayerBase):
                self.train_villager_btn.draw(screen)
            elif isinstance(selected_buildings[0], Barracks):
                for btn in self.train_buttons:
                    btn.draw(screen)
    
    def _draw_unit_info(self, screen, units, y_offset):
        if len(units) == 1:
            unit = units[0]
            unit_type = unit.__class__.__name__
            title = self.font_large.render(f"{unit_type}", True, (255, 255, 255))
        else:
            title = self.font_large.render(f"{len(units)} Unidades", True, (255, 255, 255))
        screen.blit(title, (20, y_offset))
        if len(units) <= 12:
            icon_x = 20
            icon_y = y_offset + 35
            for i, unit in enumerate(units):
                shape = UNIT_SHAPES.get(unit.__class__.__name__, 'circle')
                color = PLAYER_COLOR if not unit.is_enemy else ENEMY_COLOR
                if isinstance(unit, Villager):
                    color = VILLAGER_COLOR
                pos = Vector2(icon_x + i * 40, icon_y)
                draw_unit_shape(screen, pos, shape, color, 12, False)
                hp_percent = unit.hp / unit.max_hp
                bar_width = 20
                pygame.draw.rect(screen, (255, 0, 0), (icon_x + i * 40 - bar_width//2, icon_y + 18, bar_width, 3))
                pygame.draw.rect(screen, (0, 255, 0), (icon_x + i * 40 - bar_width//2, icon_y + 18, int(bar_width * hp_percent), 3))
        if len(units) == 1:
            unit = units[0]
            stats_y = y_offset + 65
            stats_text = [
                f"Vida: {int(unit.hp)}/{unit.max_hp}",
                f"Dano: {unit.attack_damage}",
                f"Rango: {int(unit.attack_range)}",
                f"Velocidad: {unit.speed:.1f}"
            ]
            for i, text in enumerate(stats_text):
                surf = self.font_small.render(text, True, (255, 255, 255))
                screen.blit(surf, (20 + i * 150, stats_y))
    
    def _draw_building_info(self, screen, building, y_offset):
        building_type = building.__class__.__name__
        title = self.font_large.render(f"{building_type}", True, (255, 255, 255))
        screen.blit(title, (20, y_offset))
        stats_y = y_offset + 35
        hp_text = self.font_medium.render(f"Vida: {int(building.hp)}/{building.max_hp}", True, (255, 255, 255))
        screen.blit(hp_text, (20, stats_y))
        bar_width = 200
        bar_height = 15
        bar_x = 20
        bar_y = stats_y + 30
        pygame.draw.rect(screen, (100, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        pygame.draw.rect(screen, (0, 200, 0), (bar_x, bar_y, int(bar_width * (building.hp / building.max_hp)), bar_height))
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height), 2)
        if building.under_construction:
            const_text = self.font_small.render("En construccion...", True, (255, 200, 0))
            screen.blit(const_text, (250, stats_y))
        if isinstance(building, PlayerBase) and building.villager_cooldown > 0:
            cooldown_sec = building.villager_cooldown / FPS
            cooldown_text = self.font_small.render(f"Cooldown: {int(cooldown_sec)}s", True, (200, 200, 100))
            screen.blit(cooldown_text, (250, stats_y + 20))
        if isinstance(building, Barracks) and building.queue:
            queue_y = y_offset + 35
            queue_text = self.font_medium.render(f"En cola: {len(building.queue)}", True, (255, 255, 255))
            screen.blit(queue_text, (250, queue_y))
            if building.queue:
                current_unit = building.queue[0]
                max_time = building.train_time[current_unit[0]]
                progress = 1 - (current_unit[1] / max_time)
                progress_bar_width = 150
                progress_bar_x = 250
                progress_bar_y = queue_y + 30
                pygame.draw.rect(screen, (50, 50, 50), (progress_bar_x, progress_bar_y, progress_bar_width, 15))
                pygame.draw.rect(screen, (50, 150, 255), (progress_bar_x, progress_bar_y, int(progress_bar_width * progress), 15))
                pygame.draw.rect(screen, (100, 100, 100), (progress_bar_x, progress_bar_y, progress_bar_width, 15), 2)
                percent_text = self.font_small.render(f"{int(progress * 100)}%", True, (255, 255, 255))
                screen.blit(percent_text, (progress_bar_x + progress_bar_width + 10, progress_bar_y))

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mini RTS - Enhanced")
        sprites.load_sprites()
        self.clock = pygame.time.Clock()
        self.running = True
        self.camera = Camera()
        self.minimap = Minimap(WORLD_SIZE)
        self.hud = HUD()

        player_start = Vector2(200, 200)
        enemy_start = Vector2(WORLD_SIZE - 200, WORLD_SIZE - 200)

        # 5 aldeanos para el jugador
        self.units = [
            Villager(player_start.x, player_start.y),
            Villager(player_start.x + 50, player_start.y),
            Villager(player_start.x + 100, player_start.y),
            Villager(player_start.x + 150, player_start.y),
            Villager(player_start.x + 200, player_start.y)
        ]
        # 5 aldeanos para el enemigo
        self.enemies = [
            Villager(enemy_start.x, enemy_start.y, is_enemy=True),
            Villager(enemy_start.x + 50, enemy_start.y, is_enemy=True),
            Villager(enemy_start.x + 100, enemy_start.y, is_enemy=True),
            Villager(enemy_start.x + 150, enemy_start.y, is_enemy=True),
            Villager(enemy_start.x + 200, enemy_start.y, is_enemy=True)
        ]
        
        print("Generando bosques...")
        self.trees = generate_forests(WORLD_SIZE, coverage=0.7)
        print("Limpiando camino...")
        self.trees = ensure_clear_path(self.trees, player_start, enemy_start, path_width=200)
        self.trees = [t for t in self.trees if t.pos.distance_to(player_start) > 150]
        self.trees = [t for t in self.trees if t.pos.distance_to(enemy_start) > 150]
        
        print("Generando recursos...")
        self.resources = generate_resources(WORLD_SIZE)
        
        self.player_base = PlayerBase(player_start.x, player_start.y)
        self.enemy_base = EnemyBase(enemy_start.x, enemy_start.y)
        
        enemy_barracks_pos = enemy_start + Vector2(100, 100)
        self.enemy_barracks = [Barracks(enemy_barracks_pos.x, enemy_barracks_pos.y, is_enemy=True)]
        
        self.player_barracks = []
        self.buildings_under_construction = []  # incluye ConstructionSite y edificios en construcción

        self.selection_start = None
        self.gold = 400
        self.wood = 200
        self.current_formation = 'line'
        
        print("Juego iniciado!")

        obstacle_set = set()
        update_obstacles(obstacle_set)

    def _find_free_spawn_near(self, center, min_dist, max_dist):
        for _ in range(50):
            angle = random.uniform(0, 6.28)
            dist = random.uniform(min_dist, max_dist)
            candidate = center + Vector2(dist * math.cos(angle), dist * math.sin(angle))
            if 0 < candidate.x < WORLD_SIZE and 0 < candidate.y < WORLD_SIZE:
                return candidate
        return center + Vector2(80, 80)

    def _find_free_building_spot(self, center, size, max_attempts=50):
        """Busca una posición libre para construir un edificio de tamaño 'size' alrededor de center."""
        for _ in range(max_attempts):
            angle = random.uniform(0, 2*math.pi)
            dist = random.uniform(80, 150)  # distancia de la base
            candidate = center + Vector2(dist * math.cos(angle), dist * math.sin(angle))
            # Asegurar que está dentro del mundo
            if candidate.x - size/2 < 0 or candidate.x + size/2 > WORLD_SIZE or candidate.y - size/2 < 0 or candidate.y + size/2 > WORLD_SIZE:
                continue
            # Crear rect de prueba
            test_rect = pygame.Rect(candidate.x - size/2, candidate.y - size/2, size, size)
            # Verificar colisión con edificios existentes
            collision = False
            for b in self.player_barracks + [self.player_base] + self.buildings_under_construction:
                if test_rect.colliderect(b.rect):
                    collision = True
                    break
            if collision:
                continue
            # Verificar árboles
            for tree in self.trees:
                if test_rect.collidepoint(tree.pos.x, tree.pos.y):
                    collision = True
                    break
            if not collision:
                return candidate
        return None

    def _apply_formation(self, units, target_pos):
        if not units or len(units) == 1:
            return
        formation_func = FORMATIONS.get(self.current_formation, FORMATIONS['line'])
        for i, unit in enumerate(units):
            offset = formation_func(i, len(units))
            final_pos = target_pos + offset
            unit.path = get_path(unit.pos, final_pos, set())
    
    def _enemy_ai(self):
        if self.enemy_base.hp > 0:
            self.enemy_base.update()
            if self.enemy_base.is_ready_to_train():
                for barracks in self.enemy_barracks:
                    if barracks.can_train():
                        if self.enemy_base.gold >= 200 and random.random() < 0.6:
                            barracks.train("swordsman")
                            self.enemy_base.gold -= 200
                        elif self.enemy_base.gold >= 150 and self.enemy_base.wood >= 100:
                            barracks.train("archer")
                            self.enemy_base.gold -= 150
                            self.enemy_base.wood -= 100
            for enemy in self.enemies:
                if enemy.hp <= 0:
                    continue
                if not enemy.target_entity or getattr(enemy.target_entity, "hp", 0) <= 0:
                    closest = None
                    min_dist = 600
                    for unit in self.units:
                        if unit.hp > 0:
                            d = enemy.pos.distance_to(unit.pos)
                            if d < min_dist:
                                min_dist = d
                                closest = unit
                    if not closest:
                        d_base = enemy.pos.distance_to(self.player_base.pos)
                        if d_base < 400:
                            closest = self.player_base
                    if not closest:
                        if random.random() < 0.01:
                            angle = random.uniform(0, 2*math.pi)
                            dist = random.randint(100, 300)
                            target = enemy.pos + Vector2(dist * math.cos(angle), dist * math.sin(angle))
                            target.x = max(0, min(WORLD_SIZE, target.x))
                            target.y = max(0, min(WORLD_SIZE, target.y))
                            enemy.path = get_path(enemy.pos, target, set())
                    enemy.target_entity = closest
                else:
                    dist = enemy.pos.distance_to(enemy.target_entity.pos)
                    if dist > enemy.attack_range:
                        if not enemy.path:
                            enemy.path = get_path(enemy.pos, enemy.target_entity.pos, set())

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        self.hud.update(mouse_pos, self.player_base, self.gold, self.wood)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    clicked_button = False
                    
                    # Botones de construcción (Centro y Cuartel)
                    selected_villagers = [u for u in self.units if u.selected and isinstance(u, Villager)]
                    # Nota: los botones de construcción ahora funcionan incluso sin seleccionar aldeanos, pero usaremos el más cercano
                    if self.hud.build_town_center_btn.is_clicked(mouse_pos) and self.gold >= BUILDING_COSTS['town_center']['gold']:
                        free_villagers = [u for u in self.units if isinstance(u, Villager) and u.building_target is None and u.hp > 0]
                        if free_villagers:
                            free_villagers.sort(key=lambda v: v.pos.distance_to(self.player_base.pos))
                            chosen = free_villagers[0]
                            spot = self._find_free_building_spot(self.player_base.pos, size=TILE_SIZE*3)
                            if spot:
                                site = ConstructionSite(spot.x, spot.y, 'town_center')
                                self.buildings_under_construction.append(site)
                                chosen.building_target = site
                                site.assigned_villager = chosen
                                self.gold -= BUILDING_COSTS['town_center']['gold']
                                clicked_button = True
                        else:
                            print("No hay aldeanos libres para construir")
                    
                    elif self.hud.build_barracks_btn.is_clicked(mouse_pos) and self.gold >= BUILDING_COSTS['barracks']['gold']:
                        free_villagers = [u for u in self.units if isinstance(u, Villager) and u.building_target is None and u.hp > 0]
                        if free_villagers:
                            free_villagers.sort(key=lambda v: v.pos.distance_to(self.player_base.pos))
                            chosen = free_villagers[0]
                            spot = self._find_free_building_spot(self.player_base.pos, size=TILE_SIZE*3)
                            if spot:
                                site = ConstructionSite(spot.x, spot.y, 'barracks')
                                self.buildings_under_construction.append(site)
                                chosen.building_target = site
                                site.assigned_villager = chosen
                                self.gold -= BUILDING_COSTS['barracks']['gold']
                                clicked_button = True
                        else:
                            print("No hay aldeanos libres para construir")
                    
                    # Botón de entrenar aldeano (desde la base)
                    if self.player_base.selected and self.hud.train_villager_btn.is_clicked(mouse_pos) and self.gold >= UNIT_COSTS['villager']['gold']:
                        if self.player_base.can_train_villager():
                            spawn = self._find_free_spawn_near(self.player_base.pos, 80, 120)
                            self.units.append(Villager(spawn.x, spawn.y))
                            self.gold -= UNIT_COSTS['villager']['gold']
                            self.player_base.start_train_villager()
                            clicked_button = True
                    
                    # Botones de entrenamiento de unidades (desde cuarteles)
                    selected_barracks = [b for b in self.player_barracks if b.selected]
                    if selected_barracks:
                        if self.hud.train_swordsman_btn.is_clicked(mouse_pos) and self.gold >= UNIT_COSTS['swordsman']['gold']:
                            for b in selected_barracks:
                                if b.can_train():
                                    b.train("swordsman")
                                    self.gold -= UNIT_COSTS['swordsman']['gold']
                                    clicked_button = True
                                    break
                        elif self.hud.train_archer_btn.is_clicked(mouse_pos) and self.gold >= UNIT_COSTS['archer']['gold'] and self.wood >= UNIT_COSTS['archer']['wood']:
                            for b in selected_barracks:
                                if b.can_train():
                                    b.train("archer")
                                    self.gold -= UNIT_COSTS['archer']['gold']
                                    self.wood -= UNIT_COSTS['archer']['wood']
                                    clicked_button = True
                                    break
                    
                    # Botones de formación
                    selected_units_for_formation = [u for u in self.units if u.selected]
                    if len(selected_units_for_formation) > 1:
                        if self.hud.form_line_btn.is_clicked(mouse_pos):
                            self.current_formation = 'line'
                            clicked_button = True
                        elif self.hud.form_box_btn.is_clicked(mouse_pos):
                            self.current_formation = 'box'
                            clicked_button = True
                        elif self.hud.form_column_btn.is_clicked(mouse_pos):
                            self.current_formation = 'column'
                            clicked_button = True
                        elif self.hud.form_wedge_btn.is_clicked(mouse_pos):
                            self.current_formation = 'wedge'
                            clicked_button = True
                    
                    if not clicked_button:
                        world_pos = self.minimap.world_pos_from_minimap_click(mouse_pos)
                        if world_pos:
                            self.camera.offset.x = -(world_pos.x - WIDTH / 2)
                            self.camera.offset.y = -(world_pos.y - HEIGHT / 2)
                            self.camera.offset.x = max(-(WORLD_SIZE - WIDTH), min(0, self.camera.offset.x))
                            self.camera.offset.y = max(-(WORLD_SIZE - HEIGHT), min(0, self.camera.offset.y))
                        else:
                            self.selection_start = Vector2(mouse_pos)

            if event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.selection_start:
                    end = pygame.mouse.get_pos()
                    selection_size = abs(self.selection_start.x - end[0]) + abs(self.selection_start.y - end[1])
                    is_single_click = selection_size < 10
                    
                    if is_single_click:
                        click_world_pos = Vector2(end) - self.camera.offset
                        for u in self.units:
                            u.selected = False
                        self.player_base.selected = False
                        for b in self.player_barracks + self.buildings_under_construction:
                            b.selected = False
                        found_selection = False
                        for u in self.units:
                            if u.pos.distance_to(click_world_pos) < 15:
                                u.selected = True
                                found_selection = True
                                break
                        if not found_selection:
                            if self.player_base.rect.collidepoint(click_world_pos.x, click_world_pos.y):
                                self.player_base.selected = True
                                found_selection = True
                            if not found_selection:
                                for b in self.player_barracks + self.buildings_under_construction:
                                    if b.rect.collidepoint(click_world_pos.x, click_world_pos.y):
                                        b.selected = True
                                        break
                    else:
                        rect = pygame.Rect(
                            min(self.selection_start.x, end[0]),
                            min(self.selection_start.y, end[1]),
                            abs(self.selection_start.x - end[0]),
                            abs(self.selection_start.y - end[1])
                        )
                        for u in self.units:
                            u.selected = False
                        self.player_base.selected = False
                        for b in self.player_barracks + self.buildings_under_construction:
                            b.selected = False
                        for u in self.units:
                            world_pos = u.pos
                            screen_pos = self.camera.apply(world_pos)
                            if rect.collidepoint(screen_pos.x, screen_pos.y):
                                u.selected = True
                        base_world_pos = self.player_base.pos
                        base_screen_pos = self.camera.apply(base_world_pos)
                        if rect.collidepoint(base_screen_pos.x, base_screen_pos.y):
                            self.player_base.selected = True
                        for b in self.player_barracks + self.buildings_under_construction:
                            building_world_pos = b.pos
                            building_screen_pos = self.camera.apply(building_world_pos)
                            if rect.collidepoint(building_screen_pos.x, building_screen_pos.y):
                                b.selected = True
                    
                    self.selection_start = None

                if event.button == 3:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.minimap.rect.collidepoint(mouse_pos):
                        world_pos = self.minimap.world_pos_from_minimap_click(mouse_pos)
                        if world_pos:
                            target_pos = world_pos
                        else:
                            continue
                    else:
                        target_pos = Vector2(mouse_pos) - self.camera.offset
                    
                    target_entity = None
                    for e in self.enemies:
                        if e.hp > 0 and e.pos.distance_to(target_pos) < 30:
                            target_entity = e
                            break
                    if not target_entity and self.enemy_base.hp > 0:
                        if self.enemy_base.rect.collidepoint(target_pos.x, target_pos.y):
                            target_entity = self.enemy_base
                    if not target_entity:
                        for b in self.enemy_barracks:
                            if b.rect.collidepoint(target_pos.x, target_pos.y):
                                target_entity = b
                                break
                    if not target_entity:
                        for r in self.resources:
                            if r.amount > 0 and r.pos.distance_to(target_pos) < 30:
                                target_entity = r
                                break
                    if not target_entity:
                        for tree in self.trees:
                            if tree.wood_amount > 0 and tree.pos.distance_to(target_pos) < 30:
                                target_entity = tree
                                break
                    
                    selected_units = [u for u in self.units if u.selected and u.hp > 0]
                    if len(selected_units) > 1 and not target_entity:
                        self._apply_formation(selected_units, target_pos)
                    else:
                        for u in selected_units:
                            u.target_entity = target_entity
                            if not target_entity:
                                u.path = get_path(u.pos, target_pos, set())
                            else:
                                u.path = []

    def update(self):
        pathfinding_tick()
        self.camera.update()
        
        self.player_base.update()
        
        for building in self.buildings_under_construction:
            building.update()
        
        # Comprobar obras completadas
        completed_sites = []
        for site in self.buildings_under_construction:
            if isinstance(site, ConstructionSite) and site.completed:
                # Crear el edificio real
                if site.building_type == 'town_center':
                    new_building = PlayerBase(site.pos.x, site.pos.y)
                elif site.building_type == 'barracks':
                    new_building = Barracks(site.pos.x, site.pos.y)
                # Añadir a la lista correspondiente
                if site.building_type == 'town_center':
                    # Por ahora, el jugador solo tiene una base principal, pero podría ser otra
                    self.buildings_under_construction.append(new_building)  # lo añadimos como edificio normal? Mejor lista aparte
                    # Para simplificar, lo añadimos a buildings_under_construction pero sin under_construction
                    new_building.under_construction = False
                    self.buildings_under_construction.append(new_building)
                else:
                    self.player_barracks.append(new_building)
                # Eliminar el aldeano asignado
                if site.assigned_villager and site.assigned_villager in self.units:
                    self.units.remove(site.assigned_villager)
                completed_sites.append(site)
        for site in completed_sites:
            self.buildings_under_construction.remove(site)
        
        # Actualizar edificios normales (no obras)
        for b in self.player_barracks + self.enemy_barracks:
            b.update()
        
        self._enemy_ai()
        
        all_units_and_enemies = self.units + self.enemies
        for u in self.units:
            u.update(set(), self.resources, self.player_base, all_units_and_enemies, self.trees)
        for e in self.enemies:
            e.update(set(), self.resources, self.player_base, all_units_and_enemies, self.trees)

        self.units = [u for u in self.units if u.hp > 0]
        self.enemies = [e for e in self.enemies if e.hp > 0]
        self.resources = [r for r in self.resources if r.amount > 0]
        self.trees = [t for t in self.trees if t.wood_amount > 0]
        
        for u in self.units:
            if isinstance(u, Villager):
                deposits = u.take_deposit()
                self.gold += deposits['gold']
                self.wood += deposits['wood']
        
        self.gold += 0.02

        for b in self.player_barracks + self.enemy_barracks:
            res = b.tick_queue()
            if res:
                _play_training_complete_sound()
                spawn = self._find_free_spawn_near(b.pos, 80, 120)
                if b in self.player_barracks:
                    if res == "villager":
                        self.units.append(Villager(spawn.x, spawn.y))
                    elif res == "swordsman":
                        self.units.append(Swordsman(spawn.x, spawn.y))
                    elif res == "archer":
                        self.units.append(Archer(spawn.x, spawn.y))
                else:
                    if res == "swordsman":
                        self.enemies.append(Swordsman(spawn.x, spawn.y, is_enemy=True))
                    elif res == "archer":
                        self.enemies.append(Archer(spawn.x, spawn.y, is_enemy=True))

    def draw(self):
        self.screen.fill(BG_COLOR)
        
        all_objects = []
        all_objects.extend(self.trees)
        all_objects.append(self.player_base)
        if self.enemy_base.hp > 0:
            all_objects.append(self.enemy_base)
        all_objects.extend(self.resources)
        all_objects.extend(self.player_barracks + self.enemy_barracks + self.buildings_under_construction)
        all_objects.extend(self.units + self.enemies)
        
        all_objects.sort(key=lambda obj: obj.z_order if hasattr(obj, 'z_order') else obj.pos.y)
        
        for obj in all_objects:
            obj.draw(self.screen, self.camera)
        
        if self.selection_start:
            curr = pygame.mouse.get_pos()
            pygame.draw.rect(self.screen, SELECT_COLOR, 
                           (min(self.selection_start.x, curr[0]), 
                            min(self.selection_start.y, curr[1]), 
                            abs(self.selection_start.x - curr[0]), 
                            abs(self.selection_start.y - curr[1])), 1)
        
        self.hud.draw_top_panel(self.screen, self.gold, self.wood, self.units, self.enemies, self.resources)
        
        selected_units = [u for u in self.units if u.selected]
        selected_buildings = [self.player_base] if self.player_base.selected else []
        selected_buildings.extend([b for b in self.player_barracks + self.buildings_under_construction if b.selected])
        
        self.hud.draw_bottom_panel(self.screen, selected_units, selected_buildings)
        
        self.minimap.draw(self.screen, self.camera, self.units, self.enemies, 
                         self.resources, self.player_base, self.enemy_base,
                         self.player_barracks, self.enemy_barracks, self.trees)
        
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    while game.running:
        game.handle_events()
        game.update()
        game.draw()
        game.clock.tick(FPS)
    pygame.quit()