import arcade
import pytest


def test_rotate_point():
    x = 0
    y = 0
    cx = 0
    cy = 0
    angle = 0
    rx, ry = arcade.rotate_point(x, y, cx, cy, angle)
    assert rx == 0
    assert ry == 0

    x = 0
    y = 0
    cx = 0
    cy = 0
    angle = 90
    rx, ry = arcade.rotate_point(x, y, cx, cy, angle)
    assert rx == 0
    assert ry == 0

    x = 50
    y = 50
    cx = 0
    cy = 0
    angle = 0
    rx, ry = arcade.rotate_point(x, y, cx, cy, angle)
    assert rx == 50
    assert ry == 50

    x = 50
    y = 0
    cx = 0
    cy = 0
    angle = 90
    rx, ry = arcade.rotate_point(x, y, cx, cy, angle)
    assert rx == 0
    assert ry == 50

    x = 20
    y = 10
    cx = 10
    cy = 10
    angle = 180
    rx, ry = arcade.rotate_point(x, y, cx, cy, angle)
    assert rx == 0
    assert ry == 10


def test_parse_color():
    with pytest.raises(ValueError):
        arcade.color_from_hex_string("#ff0000ff0")

    # Hash symbol RGBA variants
    assert arcade.color_from_hex_string("#ffffffff") == (255, 255, 255, 255)
    assert arcade.color_from_hex_string("#ffffff00") == (255, 255, 255, 0)
    assert arcade.color_from_hex_string("#ffff00ff") == (255, 255, 0, 255)
    assert arcade.color_from_hex_string("#ff00ffff") == (255, 0, 255, 255)
    assert arcade.color_from_hex_string("#00ffffff") == (0, 255, 255, 255)

    # RGB
    assert arcade.color_from_hex_string("#ffffff") == (255, 255, 255, 255)
    assert arcade.color_from_hex_string("#ffff00") == (255, 255, 0, 255)
    assert arcade.color_from_hex_string("#ff0000") == (255, 0, 0, 255)

    # Without hash
    assert arcade.color_from_hex_string("ffffff") == (255, 255, 255, 255)
    assert arcade.color_from_hex_string("ffff00") == (255, 255, 0, 255)
    assert arcade.color_from_hex_string("ff0000") == (255, 0, 0, 255)

    # Short form
    assert arcade.color_from_hex_string("#fff") == (255, 255, 255, 255)
    assert arcade.color_from_hex_string("FFF") == (255, 255, 255, 255)

    with pytest.raises(ValueError):
        arcade.color_from_hex_string("ppp")

    with pytest.raises(ValueError):
        arcade.color_from_hex_string("ff")
