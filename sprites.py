import pygame
from pathlib import Path

# Diccionarios globales de sprites
unit_sprites = {}
building_sprites = {}
environment_sprites = {}
resource_sprites = {}

def load_sprites():
    """Carga todos los sprites. Debe llamarse después de pygame.display.set_mode()."""
    base_path = Path("kenney_medieval-rts") / "PNG" / "Default size"
    
    if not base_path.exists():
        print(f"ERROR: La carpeta base {base_path} no existe.")
        return False
    
    success = True

    # Unidades (tamaño original ~20x26, escalamos a 32x32)
    unit_files = {
        'Villager': 'Unit/medievalUnit_01.png',
        'Swordsman': 'Unit/medievalUnit_02.png',
        'Archer': 'Unit/medievalUnit_03.png',
        'EnemyUnit': 'Unit/medievalUnit_04.png'
    }
    for name, rel_path in unit_files.items():
        full_path = base_path / rel_path
        try:
            img = pygame.image.load(str(full_path)).convert_alpha()
            img = pygame.transform.scale(img, (32, 32))
            unit_sprites[name] = img
            print(f"✓ Cargado: {name}")
        except Exception as e:
            print(f"✗ Error cargando {full_path}: {e}")
            success = False
    
    # Edificios (tamaño original ~36x42, escalamos a 64x64)
    building_files = {
        'PlayerBase': 'Structure/medievalStructure_01.png',
        'EnemyBase': 'Structure/medievalStructure_02.png',
        'Barracks': 'Structure/medievalStructure_03.png',
        'EnemyBarracks': 'Structure/medievalStructure_04.png'
    }
    for name, rel_path in building_files.items():
        full_path = base_path / rel_path
        try:
            img = pygame.image.load(str(full_path)).convert_alpha()
            img = pygame.transform.scale(img, (64, 64))
            building_sprites[name] = img
            print(f"✓ Cargado: {name}")
        except Exception as e:
            print(f"✗ Error cargando {full_path}: {e}")
            success = False
    
    # Árboles (tamaño original 14x32 a 19x46, escalamos a 48x48)
    tree_files = [
        'Environment/medievalEnvironment_01.png',
        'Environment/medievalEnvironment_02.png',
        'Environment/medievalEnvironment_03.png',
        'Environment/medievalEnvironment_04.png'  # añadimos más variedad
    ]
    environment_sprites['trees'] = []
    for rel_path in tree_files:
        full_path = base_path / rel_path
        try:
            img = pygame.image.load(str(full_path)).convert_alpha()
            img = pygame.transform.scale(img, (48, 48))
            environment_sprites['trees'].append(img)
            print(f"✓ Cargado árbol: {rel_path}")
        except Exception as e:
            print(f"✗ Error cargando {full_path}: {e}")
            success = False
    
    # Oro (usamos una gema/cofre pequeño)
    gold_candidates = [
        'Environment/medievalEnvironment_05.png',  # parece una gema
        'Environment/medievalEnvironment_13.png',  # podría ser un cofre
        'Structure/medievalStructure_12.png'       # alternativa
    ]
    
    gold_loaded = False
    for gold_path_rel in gold_candidates:
        gold_path = base_path / gold_path_rel
        if gold_path.exists():
            try:
                img = pygame.image.load(str(gold_path)).convert_alpha()
                img = pygame.transform.scale(img, (24, 24))
                resource_sprites['gold'] = img
                print(f"✓ Cargado oro: {gold_path_rel}")
                gold_loaded = True
                break
            except:
                continue
    
    if not gold_loaded:
        print("⚠ No se pudo cargar sprite para oro, se usará fallback")
        resource_sprites['gold'] = None
    
    if success:
        print("✅ Todos los sprites cargados correctamente")
    else:
        print("⚠ Algunos sprites no se cargaron, se usará fallback")
    
    return success

# No llamamos a load_sprites() aquí, se llamará desde main.py después de inicializar pygame