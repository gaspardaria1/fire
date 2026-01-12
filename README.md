3D FIRE PARTICLE SYSTEM (PYQT6 + OPENGL) IN PYTHON
=================================================

1. INTRODUCTION
---------------

This project implements a real-time 3D fire simulation using a particle system.
The application is built with PyQt6 for the graphical interface and PyOpenGL for
rendering. The fire is represented by many small particles that move upward,
fade over time, and change color depending on their age and an "energy" parameter.

The purpose of this project is to demonstrate how particle systems can simulate
natural phenomena (like fire) by combining physics-like motion, procedural
turbulence, additive blending, and color gradients.

--------------------------------------------------

2. OBJECTIVES
-------------

The main objectives of this project are:
- To create a 3D fire simulation using a particle system approach
- To render particles in real time with OpenGL
- To simulate flame motion using buoyancy, damping, and turbulence
- To map fire colors dynamically based on particle age and energy level
- To provide user interaction through a GUI slider (energy control)
- To allow camera rotation via mouse dragging

--------------------------------------------------

3. TECHNOLOGIES AND LIBRARIES USED
---------------------------------

The project is developed using Python 3 and the following libraries:

- PyQt6
  Used for window creation, UI elements (slider, labels), event handling,
  and an OpenGL-capable widget (QOpenGLWidget).

- PyOpenGL (OpenGL.GL, OpenGL.GLU)
  Used for 3D rendering: lighting setup, blending, drawing spheres, etc.

- dataclasses
  Used to define a clean particle structure (FireParticle).

- random, math
  Used for randomized spawning, turbulence computation, and trigonometry.

--------------------------------------------------

4. PARTICLE SYSTEM CONCEPT
--------------------------

The fire is modeled as a collection of particles.
Each particle represents a small glowing "piece" of the flame.

A particle has:
- position (3D vector)
- velocity (3D vector)
- lifetime remaining
- initial lifetime
- radius (size)
- a random seed (for per-particle variation)

As time passes:
- particles rise upward
- they spread slightly sideways
- they fade/darken near the end of life
- dead particles are removed
- new particles are continuously spawned

--------------------------------------------------

5. FIREPARTICLE DATA STRUCTURE
------------------------------

Dataclass: FireParticle

Fields:
- pos: QVector3D
  Current position of the particle in 3D space.

- vel: QVector3D
  Current velocity in 3D space.

- life: float
  Remaining lifetime in seconds.

- life0: float
  Initial lifetime, used to compute normalized age.

- radius: float
  Sphere radius used when rendering.

- seed: float
  Random seed used for unique turbulence behavior per particle.

--------------------------------------------------

6. MAIN RENDERING COMPONENT (FIREWIDGET)
---------------------------------------

Class: FireWidget(QOpenGLWidget)

This is the OpenGL drawing surface and simulation controller.

Responsibilities:
- Initialize OpenGL state (depth test, blending, lighting)
- Render the particles in paintGL()
- Maintain particle list and update their physics each tick
- Handle mouse dragging for camera rotation
- Control fire "energy" (0..1), which affects color and behavior

--------------------------------------------------

7. OPENGL SETUP
---------------

Method: initializeGL()

Key OpenGL settings:
- glEnable(GL_DEPTH_TEST)
  Enables correct 3D depth handling.

- glClearColor(0.02, 0.02, 0.05, 1.0)
  Dark background for better contrast.

- Lighting enabled (GL_LIGHTING, GL_LIGHT0)
  Subtle lighting exists, but particles are mainly driven by color + blending.

- Blending enabled (GL_BLEND)
  Fire uses additive blending:
  glBlendFunc(GL_SRC_ALPHA, GL_ONE)

Additive blending makes bright overlapping particles glow, creating a flame look.

--------------------------------------------------

8. CAMERA AND VIEW TRANSFORM
----------------------------

Method: paintGL()

Camera transformations:
- Move camera back and slightly down:
  glTranslatef(0.0, -0.2, -5.0)

- Rotate camera based on mouse input:
  glRotatef(rot_x, 1, 0, 0)
  glRotatef(rot_y, 0, 1, 0)

The user rotates the view by dragging with the left mouse button.

--------------------------------------------------

9. PARTICLE RENDERING STRATEGY
------------------------------

Particles are rendered as small spheres (GLU spheres).

Rendering improvements:
- Sorting back-to-front (approx) for nicer blending
- Disabling depth writes while drawing particles:
  glDepthMask(GL_FALSE)

This avoids particles incorrectly blocking each other and improves visual layering.

Each particle color depends on:
- global energy (slider)
- particle age (from birth to death)

Alpha also depends on age:
- stronger when new
- weaker when old

--------------------------------------------------

10. FIRE COLOR MAPPING (ENERGY + AGE)
------------------------------------

Method: _fire_color(energy, age01)

Inputs:
- energy: 0..1 (from slider)
- age01:  0..1 (0 = new particle, 1 = near death)

Behavior:
- Low energy flames are mostly red/orange/yellow
- High energy flames shift toward blue/cyan/white
- As particles age, the color transitions from "hot" to "tip"
- Near the end of life, particles darken (fade effect)

This produces a visually realistic gradient flame effect.

--------------------------------------------------

11. SIMULATION LOOP (TIMER-BASED)
---------------------------------

The simulation uses a QTimer:

- dt = 1/120 (fixed-ish timestep)
- timer triggers tick() approximately every ~8 ms

Method: tick()
1. Spawn new particles
2. Update particle physics
3. Trigger repaint (update())

This creates continuous animation in real time.

--------------------------------------------------

12. PARTICLE SPAWNING
---------------------

Method: _spawn_particles()

Spawn rate depends on energy:
- low energy = fewer particles
- high energy = more particles

For each spawned particle:
- position starts near a burner disk around (0, -1, 0)
- upward velocity increases with energy
- sideways turbulence increases with energy
- lifetime is slightly longer at high energy
- radius changes with energy (hotter looks tighter/finer)

A hard cap limits total particles to 2500 for performance.

--------------------------------------------------

13. PARTICLE PHYSICS UPDATE
---------------------------

Method: _update_particles(dt)

For each particle:
1. Decrease life
2. Remove if dead
3. Apply buoyancy (upward acceleration)
4. Apply turbulence (sin/cos pseudo-noise in x/z)
5. Apply damping (slows velocity slightly over time)
6. Update position using velocity
7. Slowly increase radius (expansion effect)
8. Apply gentle centering force (keeps flame near origin)

Physics parameters depend on energy:
- buoyancy increases with energy
- swirl/turbulence increases with energy
- damping slightly changes to keep the flame lively

--------------------------------------------------

14. VISUAL REFERENCE OBJECTS
----------------------------

Optional visual helpers:

A) Burner disk
Method: _draw_burner()
- A translucent disk at y = -1.0 to indicate where particles spawn.

B) Faint bounding box
Method: _draw_faint_box(s)
- Draws a subtle cube wireframe so the user perceives depth and 3D space.

--------------------------------------------------

15. USER INTERFACE (CONTROL BAR)
--------------------------------

Class: ControlBar(QWidget)

Contains:
- Slider labeled "Energy" ranging from 0 to 100
- Label displaying the current energy value (0.00 .. 1.00)
- Hint text: "Low=Red High=Blue (drag mouse to rotate)"

When slider changes:
- energy is updated in FireWidget
- color/behavior adjusts instantly in real time

--------------------------------------------------

16. MAIN WINDOW STRUCTURE
-------------------------

Class: MainWindow(QWidget)

Layout:
- Top: ControlBar (energy slider + labels)
- Bottom: FireWidget (3D OpenGL scene)

Window title:
"3D Fire - Energy Color (PyQt6 + OpenGL)"

--------------------------------------------------

17. ADVANTAGES OF THE PROJECT
-----------------------------

- Real-time interactive 3D simulation
- Simple but effective particle system design
- Additive blending produces convincing flame glow
- Energy slider allows instant visual experimentation
- Mouse rotation makes it easy to explore the 3D scene
- Performance-friendly due to particle count capping

--------------------------------------------------

18. LIMITATIONS
---------------

- Particles are rendered as spheres (could be heavy for very large counts)
- Turbulence is procedural (sin/cos), not true noise (e.g., Perlin/Simplex)
- No smoke simulation
- No texture-based particles or billboard sprites (common in game engines)
- Lighting is minimal; appearance mainly depends on blending

--------------------------------------------------

19. POSSIBLE EXTENSIONS
-----------------------

Possible future improvements include:
- Replace spheres with textured billboards for better performance
- Add smoke particles with alpha blending (non-additive)
- Use real noise functions (Perlin/Simplex) for smoother turbulence
- Add wind control and directional airflow
- Add particle collisions or interaction with objects
- Add flame intensity flickering over time
- Add FPS counter and performance controls

--------------------------------------------------

20. CONCLUSION
--------------

This project demonstrates a classic particle system approach to simulating fire in 3D.
By combining randomized particle spawning, buoyancy-driven motion, turbulence, and
age-based color fading with additive blending, the program produces a convincing and
interactive flame effect. The energy slider and mouse rotation make it a practical
and educational example of real-time graphics with PyQt6 and OpenGL.
