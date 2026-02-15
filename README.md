# Mini RTS Engine

Un motor de juego de estrategia en tiempo real simple desarrollado en Python utilizando la librería **Pygame**.

## Características
* **Pathfinding A*:** Las unidades encuentran su camino evitando obstáculos.
* **Cámara con Scroll:** Navega por un mundo de 2000x2000 píxeles.
* **Sistema de Combate:** Unidades aliadas y enemigas con salud y daño.
* **Economía Pasiva:** Generación de oro para entrenar nuevas unidades.
* **Selección por Cuadro:** Selecciona múltiples unidades arrastrando el ratón.

## Instalación
1. Asegúrate de tener Python 3.10+ instalado.
2. Instala Pygame:
   ```bash
   pip install pygame
Ejecuta el juego:

Bash
python main.py

## Controles

Click Izquierdo: Seleccionar unidad / Arrastrar para selección múltiple.

Click Derecho: Ordenar movimiento o ataque.

Tecla U: Entrenar unidad (debe estar la base seleccionada).

Bordes de pantalla: Mover la cámara.


### Resumen de cambios aplicados:
* **Desacoplamiento:** Ahora `Unit` no necesita conocer la instancia global `Game`, simplemente recibe los obstáculos.
* **Claridad:** Cada archivo tiene un propósito claro.
* **Escalabilidad:** Es mucho más fácil añadir nuevos tipos de unidades en `entities.py` sin romper el bucle principal.