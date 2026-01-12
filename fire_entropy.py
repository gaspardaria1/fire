import sys
import random
import math
from dataclasses import dataclass

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtGui import QVector3D

from OpenGL.GL import *
from OpenGL.GLU import *


@dataclass
class FireParticle:
    pos: QVector3D
    vel: QVector3D
    life: float         # seconds remaining
    life0: float        # initial life
    radius: float
    seed: float         # for slight per-particle variation


class FireWidget(QOpenGLWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.particles: list[FireParticle] = []

        # energy in [0..1]
        self.energy = 0.5

        # camera rotation
        self.rot_x = 18
        self.rot_y = 35
        self.last_mouse_pos = None
        self.is_dragging = False

        # timing
        self.dt = 1.0 / 120.0  # fixed-ish timestep
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(8)

    # ---------- Color mapping ----------
    def _clamp01(self, x: float) -> float:
        return max(0.0, min(1.0, x))

    def _lerp(self, a: float, b: float, t: float) -> float:
        return a + (b - a) * t

    def _lerp_color(self, c0, c1, t: float):
        t = self._clamp01(t)
        return (
            self._lerp(c0[0], c1[0], t),
            self._lerp(c0[1], c1[1], t),
            self._lerp(c0[2], c1[2], t),
        )

    def _fire_color(self, energy: float, age01: float):
        """
        energy: 0..1 (slider)
        age01:  0..1 (0 = new particle, 1 = near death)

        Low energy -> more red/orange.
        High energy -> more blue.
        We also fade towards darker as particle ages.
        """
        energy = self._clamp01(energy)
        age01 = self._clamp01(age01)

        # Base palettes (tuned for "fire look"):
        # low energy: red -> orange -> yellow/white
        low_hot = (1.00, 0.15, 0.05)   # deep red
        low_mid = (1.00, 0.55, 0.10)   # orange
        low_tip = (1.00, 0.95, 0.25)   # yellowish

        # high energy: blue -> cyan -> white-ish
        high_hot = (0.10, 0.25, 1.00)  # blue
        high_mid = (0.10, 0.95, 1.00)  # cyan
        high_tip = (0.90, 0.95, 1.00)  # near white

        # Interpolate palette by energy:
        hot = self._lerp_color(low_hot, high_hot, energy)
        mid = self._lerp_color(low_mid, high_mid, energy)
        tip = self._lerp_color(low_tip, high_tip, energy)

        # Within a particle lifetime, start "hot", then go to "mid", then to "tip"
        # age01 ~ 0 -> hot, around 0.5 -> mid, near 1 -> tip
        if age01 < 0.5:
            t = age01 / 0.5
            rgb = self._lerp_color(hot, mid, t)
        else:
            t = (age01 - 0.5) / 0.5
            rgb = self._lerp_color(mid, tip, t)

        # Fade/darken near the end to look like dissipation
        fade = 1.0 - (age01 ** 1.6) * 0.75
        return (rgb[0] * fade, rgb[1] * fade, rgb[2] * fade)

    # ---------- OpenGL ----------
    def initializeGL(self):
        glEnable(GL_DEPTH_TEST)

        glClearColor(0.02, 0.02, 0.05, 1.0)

        # Lighting (subtle; particles use color + blending more than specular)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_COLOR_MATERIAL)

        glLightfv(GL_LIGHT0, GL_POSITION, [1, 1, 1, 0])
        glLightfv(GL_LIGHT0, GL_DIFFUSE,  [0.9, 0.9, 1.0, 1.0])

        # Blending for fire (additive looks like glow)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, w / max(h, 1), 0.1, 100.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        # camera
        glTranslatef(0.0, -0.2, -5.0)
        glRotatef(self.rot_x, 1, 0, 0)
        glRotatef(self.rot_y, 0, 1, 0)

        # draw simple ground/burner reference (optional)
        self._draw_burner()

        # render particles back-to-front for nicer blending (approx)
        cam_dir = QVector3D(0, 0, 1)
        parts_sorted = sorted(
            self.particles,
            key=lambda p: QVector3D.dotProduct(p.pos, cam_dir),
            reverse=True
        )

        glDisable(GL_LIGHTING)  # fire looks better without hard lighting
        glDepthMask(GL_FALSE)   # so blending layers nicely

        for p in parts_sorted:
            age01 = 1.0 - (p.life / max(p.life0, 1e-6))
            r, g, b = self._fire_color(self.energy, age01)

            # alpha: stronger when new, softer when old
            alpha = 0.18 * (1.0 - age01) + 0.02

            self._draw_sphere(p.pos.x(), p.pos.y(), p.pos.z(), p.radius, (r, g, b), alpha)

        glDepthMask(GL_TRUE)

        # outline a faint bounding box so you "see" 3D space (optional)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._draw_faint_box(1.2)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    def _draw_sphere(self, x, y, z, radius, color_rgb, alpha):
        glPushMatrix()
        glTranslatef(x, y, z)

        glColor4f(color_rgb[0], color_rgb[1], color_rgb[2], alpha)

        quad = gluNewQuadric()
        gluSphere(quad, radius, 12, 12)
        gluDeleteQuadric(quad)

        glPopMatrix()

    def _draw_burner(self):
        # A small “burner” disk at origin
        glDisable(GL_LIGHTING)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glColor4f(0.6, 0.6, 0.7, 0.35)
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0.0, -1.0, 0.0)
        R = 0.35
        for i in range(0, 41):
            a = (i / 40.0) * math.tau
            glVertex3f(math.cos(a) * R, -1.0, math.sin(a) * R)
        glEnd()
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    def _draw_faint_box(self, s: float):
        glDisable(GL_LIGHTING)
        glColor4f(0.6, 0.75, 1.0, 0.07)
        glBegin(GL_LINES)

        # 12 edges of cube
        corners = [
            (-s, -s, -s), ( s, -s, -s), ( s,  s, -s), (-s,  s, -s),
            (-s, -s,  s), ( s, -s,  s), ( s,  s,  s), (-s,  s,  s),
        ]
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),
            (4, 5), (5, 6), (6, 7), (7, 4),
            (0, 4), (1, 5), (2, 6), (3, 7)
        ]

        for a, b in edges:
            glVertex3f(*corners[a])
            glVertex3f(*corners[b])

        glEnd()

    # ---------- Simulation ----------
    def tick(self):
        self._spawn_particles()
        self._update_particles(self.dt)
        self.update()

    def _spawn_particles(self):
        """
        Spawn rate depends on energy.
        """
        e = self.energy
        # particles per tick (on average)
        spawn_float = self._lerp(1.5, 10.0, e)
        count = int(spawn_float)
        if random.random() < (spawn_float - count):
            count += 1

        for _ in range(count):
            # spawn near burner (x,z around 0)
            r = 0.18 + 0.10 * (1.0 - e)
            angle = random.random() * math.tau
            rad = (random.random() ** 0.6) * r
            x = math.cos(angle) * rad
            z = math.sin(angle) * rad
            y = -1.0 + random.uniform(0.0, 0.05)

            # upward velocity increases with energy
            base_up = self._lerp(0.9, 2.4, e)
            vy = random.uniform(base_up * 0.6, base_up * 1.1)

            # sideways turbulence
            side = self._lerp(0.45, 0.9, e)
            vx = random.uniform(-side, side)
            vz = random.uniform(-side, side)

            # lifetime slightly longer at higher energy
            life0 = random.uniform(self._lerp(0.55, 0.85, e), self._lerp(0.85, 1.25, e))

            # radius changes with energy (hotter = a bit tighter +  finer)
            radius = random.uniform(self._lerp(0.045, 0.030, e), self._lerp(0.070, 0.050, e))

            p = FireParticle(
                pos=QVector3D(x, y, z),
                vel=QVector3D(vx, vy, vz),
                life=life0,
                life0=life0,
                radius=radius,
                seed=random.random() * 9999.0
            )
            self.particles.append(p)

        # cap count to keep it fast
        if len(self.particles) > 2500:
            self.particles = self.particles[-2500:]

    def _update_particles(self, dt: float):
        """
        Buoyancy upward + turbulence + damping.
        """
        e = self.energy

        buoyancy = self._lerp(1.2, 3.2, e)     # upward accel
        swirl = self._lerp(0.8, 2.1, e)        # turbulence strength
        damping = self._lerp(0.985, 0.992, e)  # keep it lively

        alive = []
        t = (self.timer.remainingTime() % 1000) / 1000.0  # small changing number

        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue

            age01 = 1.0 - (p.life / max(p.life0, 1e-6))

            # buoyancy (accelerate upward)
            p.vel.setY(p.vel.y() + buoyancy * dt)

            # turbulence (simple pseudo-noise based on sin/cos)
            # makes flame "dance" in x/z
            phase = (p.seed * 0.001) + (age01 * 6.0) + t * 3.0
            tx = math.sin(phase * 3.7) * math.cos(phase * 1.9)
            tz = math.cos(phase * 2.9) * math.sin(phase * 2.3)

            p.vel.setX(p.vel.x() + tx * swirl * dt)
            p.vel.setZ(p.vel.z() + tz * swirl * dt)

            # damping
            p.vel *= damping

            # rise + spread slightly with age
            p.pos += p.vel * dt

            # as it rises, it expands a bit and fades
            p.radius *= (1.0 + 0.25 * dt)

            # soft "world bounds" to keep it centered (optional)
            # pull towards center a bit
            p.pos.setX(p.pos.x() * 0.999)
            p.pos.setZ(p.pos.z() * 0.999)

            alive.append(p)

        self.particles = alive

    # ---------- Mouse rotate ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.position()

    def mouseMoveEvent(self, event):
        if self.is_dragging and self.last_mouse_pos is not None:
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()
            self.rot_x += dy * 0.5
            self.rot_y += dx * 0.5
            self.last_mouse_pos = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = False


class ControlBar(QWidget):
    def __init__(self, fire_widget: FireWidget):
        super().__init__()
        self.fire_widget = fire_widget

        layout = QHBoxLayout()
        layoutlayout = layout
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Energy:"))

        self.energy_slider = QSlider(Qt.Orientation.Horizontal)
        self.energy_slider.setRange(0, 100)
        self.energy_slider.setValue(50)
        self.energy_slider.setMinimumWidth(320)
        self.energy_slider.valueChanged.connect(self.on_energy_changed)
        layout.addWidget(self.energy_slider, stretch=1)

        self.energy_label = QLabel("0.50")
        self.energy_label.setMinimumWidth(60)
        layout.addWidget(self.energy_label)

        hint = QLabel("Low=Red  High=Blue   (drag mouse to rotate)")
        hint.setStyleSheet("opacity: 0.85;")
        layout.addWidget(hint)

        self.setLayout(layout)
        self.on_energy_changed()

    def on_energy_changed(self):
        e = self.energy_slider.value() / 100.0
        self.fire_widget.energy = e
        self.energy_label.setText(f"{e:.2f}")


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Fire - Energy Color (PyQt6 + OpenGL)")

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        self.fire_widget = FireWidget()
        self.control_bar = ControlBar(self.fire_widget)

        main_layout.addWidget(self.control_bar, stretch=0)
        main_layout.addWidget(self.fire_widget, stretch=1)

        self.setLayout(main_layout)
        self.resize(1100, 750)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())
