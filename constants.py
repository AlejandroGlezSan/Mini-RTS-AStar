from pygame import Vector2

WIDTH, HEIGHT = 1200, 800
WORLD_SIZE = 2000 
TILE_SIZE = 40
FPS = 60

# Colores
BG_COLOR = (30, 30, 30)
SELECT_COLOR = (0, 255, 0)
UNIT_COLOR = (0, 100, 255)
ENEMY_COLOR = (255, 50, 50)
OBSTACLE_COLOR = (200, 50, 50)
BASE_COLOR = (150, 150, 150)
UI_COLOR = (255, 255, 255)

# Formas de unidades (fallback si no hay sprite)
UNIT_SHAPES = {
    'Villager': 'circle',
    'Swordsman': 'triangle',
    'Archer': 'square',
    'EnemyUnit': 'diamond'
}

# Colores de equipo
PLAYER_COLOR = (0, 120, 255)
ENEMY_COLOR = (255, 50, 50)
VILLAGER_COLOR = (200, 200, 100)

# Formaciones
FORMATION_SPACING = 50
FORMATIONS = {
    'line': lambda idx, count: Vector2((idx - count/2) * FORMATION_SPACING, 0),
    'box': lambda idx, count: Vector2(
        (idx % int(count**0.5 + 1) - int(count**0.5 + 1)/2) * FORMATION_SPACING,
        (idx // int(count**0.5 + 1) - int(count**0.5 + 1)/2) * FORMATION_SPACING
    ),
    'column': lambda idx, count: Vector2(0, (idx - count/2) * FORMATION_SPACING),
    'wedge': lambda idx, count: Vector2(
        (abs(idx - count/2)) * FORMATION_SPACING * 0.7,
        (idx - count/2) * FORMATION_SPACING * 0.5
    )
}

# Velocidades
VILLAGER_SPEED = 1.0
UNIT_SPEED = 1.2
ARCHER_SPEED = 1.3

# Velocidad de recolección
GATHER_RATE = 0.15

# Separación entre unidades (ajustado para evitar solapamiento)
SEPARATION_RADIUS = 40          # antes 30
SEPARATION_WEIGHT = 2.0         # antes 1.2

# Costos y tiempos de construcción
BUILDING_COSTS = {
    'town_center': {'gold': 400, 'wood': 0, 'time': 120 * FPS},
    'barracks': {'gold': 150, 'wood': 0, 'time': 60 * FPS}
}

# Costos y tiempos de entrenamiento
UNIT_COSTS = {
    'villager': {'gold': 50, 'wood': 0, 'time': 15 * FPS},
    'swordsman': {'gold': 200, 'wood': 0, 'time': 60 * FPS},
    'archer': {'gold': 150, 'wood': 100, 'time': 90 * FPS}
}