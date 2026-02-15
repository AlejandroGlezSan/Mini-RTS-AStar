import heapq
from pygame import Vector2
from constants import TILE_SIZE, WORLD_SIZE

# Caché de rutas: clave = (start_node, goal_node), valor = list[Vector2]
_path_cache = {}
# TTL por entrada de caché (en frames)
_cache_ttl = {}
_DEFAULT_TTL = 300

# Grid de obstáculos (booleano) y dimensiones en tiles
_obstacle_grid = None
_grid_width = WORLD_SIZE // TILE_SIZE
_grid_height = WORLD_SIZE // TILE_SIZE

def _build_obstacle_grid(obstacles):
    """
    Construye una matriz 2D (lista de listas) booleana donde True indica obstáculo.
    `obstacles` se espera como un conjunto de tuplas (x_tile, y_tile).
    """
    global _obstacle_grid
    grid = [[False for _ in range(_grid_height)] for _ in range(_grid_width)]
    for (x, y) in obstacles:
        if 0 <= x < _grid_width and 0 <= y < _grid_height:
            grid[x][y] = True
    _obstacle_grid = grid

def update_obstacles(obstacles):
    """
    Función pública para reconstruir la grilla de obstáculos cuando cambian.
    También limpia la caché de rutas porque las rutas previas pueden quedar inválidas.
    """
    global _path_cache, _cache_ttl
    _build_obstacle_grid(obstacles)
    _path_cache.clear()
    _cache_ttl.clear()

def heuristic(a, b):
    # Distancia Manhattan en nodos (suficiente para A* con movimiento 8-direcciones)
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def _reconstruct_path(came_from, current):
    path = []
    while current in came_from:
        path.append(Vector2(current[0] * TILE_SIZE + TILE_SIZE // 2,
                            current[1] * TILE_SIZE + TILE_SIZE // 2))
        current = came_from[current]
    path.reverse()
    return path

def invalidate_paths_to(goal_node):
    """
    Elimina de la caché todas las rutas cuyo goal_node coincide con el pasado.
    goal_node: tupla (x_tile, y_tile)
    """
    global _path_cache, _cache_ttl
    keys_to_remove = [k for k in _path_cache.keys() if k[1] == goal_node]
    for k in keys_to_remove:
        _path_cache.pop(k, None)
        _cache_ttl.pop(k, None)

def tick():
    """
    Decrementa TTL de entradas en caché y elimina las expiradas.
    Llamar una vez por frame desde el bucle principal (Game.update).
    """
    global _cache_ttl, _path_cache
    expired = []
    for k in list(_cache_ttl.keys()):
        _cache_ttl[k] -= 1
        if _cache_ttl[k] <= 0:
            expired.append(k)
    for k in expired:
        _cache_ttl.pop(k, None)
        _path_cache.pop(k, None)

def get_path(start, goal, obstacles):
    """
    Devuelve una lista de Vector2 representando el centro de los tiles desde start hasta goal.
    - start, goal: Vector2 en coordenadas de píxel.
    - obstacles: conjunto de tuplas (x_tile, y_tile) o None.
    Implementa:
    - Construcción de grilla de obstáculos (si no existe o si se pasa un conjunto distinto).
    - Caché simple por par (start_node, goal_node) con TTL.
    """
    global _path_cache, _obstacle_grid, _cache_ttl

    # Convertir a nodos de grilla
    start_node = (int(start[0] // TILE_SIZE), int(start[1] // TILE_SIZE))
    goal_node = (int(goal[0] // TILE_SIZE), int(goal[1] // TILE_SIZE))

    # Validar nodos dentro del mundo
    if not (0 <= start_node[0] < _grid_width and 0 <= start_node[1] < _grid_height):
        return []
    if not (0 <= goal_node[0] < _grid_width and 0 <= goal_node[1] < _grid_height):
        return []

    # Si no hay grilla construida, construirla
    if _obstacle_grid is None:
        _build_obstacle_grid(obstacles)

    # Si el objetivo o inicio están bloqueados, no hay camino
    if _obstacle_grid[start_node[0]][start_node[1]] or _obstacle_grid[goal_node[0]][goal_node[1]]:
        return []

    cache_key = (start_node, goal_node)
    if cache_key in _path_cache:
        return list(_path_cache[cache_key])  # devolver copia para evitar mutaciones externas

    # A* sobre la grilla
    open_heap = []
    heapq.heappush(open_heap, (0, start_node))
    came_from = {}
    gscore = {start_node: 0}

    while open_heap:
        current = heapq.heappop(open_heap)[1]
        if current == goal_node:
            path = _reconstruct_path(came_from, current)
            _path_cache[cache_key] = path
            _cache_ttl[cache_key] = _DEFAULT_TTL
            return list(path)

        # Vecinos 8-direcciones
        for i, j in [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]:
            nx, ny = current[0] + i, current[1] + j
            if not (0 <= nx < _grid_width and 0 <= ny < _grid_height):
                continue
            if _obstacle_grid[nx][ny]:
                continue

            tentative_g = gscore[current] + (1.41 if i != 0 and j != 0 else 1)
            neighbor = (nx, ny)
            if tentative_g < gscore.get(neighbor, float('inf')):
                came_from[neighbor] = current
                gscore[neighbor] = tentative_g
                fscore = tentative_g + heuristic(neighbor, goal_node)
                heapq.heappush(open_heap, (fscore, neighbor))

    # Si no se encuentra camino, cachear lista vacía para evitar recomputaciones inmediatas
    _path_cache[cache_key] = []
    _cache_ttl[cache_key] = _DEFAULT_TTL // 4
    return []