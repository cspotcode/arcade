import math
import sys
import arcade
import pyglet
import pyglet.experimental.geoshader_sprite
import random
import time
import statprof
import psutil

# Does not work on Windows.  Might work on Linux
use_statprof = False

print(sys.argv)
is_pyglet_geosprite = False
if sys.argv[1] == 'arcade':
    is_arcade = True
elif sys.argv[1] == 'pyglet_sprite':
    is_arcade = False
elif sys.argv[1] == 'pyglet_geosprite':
    is_arcade = False
    is_pyglet_geosprite = True
else:
    raise Exception('')


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

WALL_DIM_MIN = 10
WALL_DIM_MAX = 200
WALLS_COUNT = 10

BULLET_VELOCITY_MIN = 1/60
BULLET_VELOCITY_MAX = 10/60
BULLET_COUNT = 9000

SIMULATE_MINUTES = 3
SIMULATE_FPS = 60

# Predictable randomization so that each benchmark is identical
rng = random.Random(0)

bullets = arcade.SpriteList(use_spatial_hash=False) if is_arcade else []

window = arcade.Window()

# Seed chosen manually to create a wall distribution that looked good enough,
# like something I might create in a game.
rng.seed(2)

png_path = 'benchmarks/arcade-spritelist-vs-pyglet-batch/image.png'
arcade_texture = arcade.load_texture(png_path)
def create_bullet_arcade():
    # Create a new bullet
    new_bullet = arcade.Sprite(path_or_texture=arcade_texture)
    new_bullet.position = (rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT))
    speed = rng.random() * (BULLET_VELOCITY_MAX - BULLET_VELOCITY_MIN) + BULLET_VELOCITY_MIN
    angle = rng.random() * math.pi * 2
    new_bullet.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
    # Half of bullets are rotated, to test those code paths
    if rng.random() > 0.5:
        new_bullet.angle = 45
    return new_bullet

pyglet_batch = pyglet.graphics.Batch()
pyglet_image = pyglet.image.load(png_path)

class MyPygletSprite(pyglet.experimental.geoshader_sprite.Sprite):
    __slots__ = ['velocity']

PygletSpriteImpl = MyPygletSprite if is_pyglet_geosprite else pyglet.sprite.Sprite
def create_bullet_pyglet():
    # Create a new bullet
    new_bullet = PygletSpriteImpl(img=pyglet_image, batch=pyglet_batch, subpixel=True)
    new_bullet.position = (rng.randint(0, SCREEN_WIDTH), rng.randint(0, SCREEN_HEIGHT), 0)
    speed = rng.random() * (BULLET_VELOCITY_MAX - BULLET_VELOCITY_MIN) + BULLET_VELOCITY_MIN
    angle = rng.random() * math.pi * 2
    new_bullet.velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
    # Half of bullets are rotated, to test those code paths
    if rng.random() > 0.5:
        new_bullet.rotation = 45
    return new_bullet

def move_bullets_arcade():
    # Move all bullets
    for bullet in bullets:
        x, y = bullet.position
        bullet.position = (x + bullet.velocity[0], y + bullet.velocity[1])
def move_bullets_pyglet():
    # Move all bullets
    for bullet in bullets:
        x, y, _ = bullet.position
        bullet.position = (x + bullet.velocity[0], y + bullet.velocity[1], 0)


def draw_bullets_arcade():
    bullets.draw()

def draw_bullets_pyglet():
    pyglet_batch.draw()

create_bullet = create_bullet_arcade if is_arcade else create_bullet_pyglet
move_bullets = move_bullets_arcade if is_arcade else move_bullets_pyglet
draw_bullets = draw_bullets_arcade if is_arcade else draw_bullets_pyglet

for i in range(0, BULLET_COUNT):
    bullets.append(create_bullet())

if use_statprof:
    statprof.start()

for i in range(0, int(SIMULATE_MINUTES * 60 * SIMULATE_FPS)):
    pyglet.clock.tick()

    window.switch_to()
    window.dispatch_events()

    move_bullets()
    window.dispatch_event('on_draw')

    window.clear(color=arcade.color.WHITE)
    draw_bullets()
    window.flip()

if use_statprof:
    statprof.stop()
    statprof.display()

print(psutil.Process().memory_info().rss / (1024 * 1024))
