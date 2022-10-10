"""
Camera class
"""
import math
from typing import Optional, Tuple, Union

from pyglet.math import Mat4, Vec2, Vec3

import arcade

# type aliases
FourIntTuple = Tuple[int, int, int, int]
FourFloatTuple = Tuple[float, float, float, float]


class BaseCamera:
    """
    A simple camera that allows to change the viewport, the projection and can move around.
    That's it.
    See arcade.AdvanceCamera for more advance stuff.

    :param viewport: Size of the viewport: (left, bottom, width, height)
    :param projection: Space to allocate in the viewport of the camera (left, right, bottom, top)
    """

    def __init__(self, viewport: FourIntTuple = None, projection: FourFloatTuple = None) -> None:
        self._window = arcade.get_window()

        # store the viewport and projection tuples
        self._viewport: FourIntTuple = viewport or (0, 0, self._window.width, self._window.height)
        self._projection: FourFloatTuple = projection or (0, self._window.width, 0, self._window.height)

        # Matrixes
        # Projection Matrix is used to apply the camera viewport size
        self._projection_matrix: Mat4 = Mat4()
        # View Matrix is what the camera is looking at(position)
        self._view_matrix: Mat4 = Mat4()
        # We multiply projection and view matrices to get combined, this is what actually gets sent to GL context
        self._combined_matrix: Mat4 = Mat4()

        # Position
        self.position: Vec2 = Vec2(0, 0)

        # Movement Speed, 1.0 is instant
        self.goal_position: Vec2 = Vec2(0, 0)
        self.move_speed: float = 1.0
        self.moving: bool = False

        # Init matrixes
        # This will precompute the projection, view and combined matrixes
        self._set_projection_matrix(update_combined_matrix=False)
        self._set_view_matrix()

    @property
    def viewport_width(self) -> int:
        """ Returns the width of the viewport """
        return self._viewport[2]

    @property
    def viewport_height(self) -> int:
        """ Returns the height of the viewport """
        return self._viewport[3]

    @property
    def viewport(self) -> FourIntTuple:
        return self._viewport

    @viewport.setter
    def viewport(self, viewport: FourIntTuple) -> None:
        self._viewport = viewport

    @property
    def projection(self) -> FourFloatTuple:
        return self._projection

    @projection.setter
    def projection(self, new_projection: FourFloatTuple) -> None:
        self._projection = new_projection
        self._set_projection_matrix()

    def _set_projection_matrix(self, *, update_combined_matrix: bool = True) -> None:
        """
        Helper method. This will just precompute the projection and combined matrix

        :param bool update_combined_matrix: if True will also update the combined matrix (projection @ view)
        """
        self._projection_matrix = Mat4.orthogonal_projection(*self._projection, -1, 1)
        if update_combined_matrix:
            self._set_combined_matrix()

    def _set_view_matrix(self) -> None:
        """ Helper method. This will just precompute the view and combined matrix"""

        # Figure out our 'real' position
        result_position = Vec3(
            (self.position[0] / (self.viewport_width / 2)),
            (self.position[1] / (self.viewport_height / 2)),
            0
        )
        self._view_matrix = ~(Mat4.from_translation(result_position))
        self._set_combined_matrix()

    def _set_combined_matrix(self) -> None:
        """ Helper method. This will just precompute the combined matrix"""
        self._combined_matrix = self._projection_matrix @ self._view_matrix

    def move_to(self, vector: Vec2, speed: float = 1.0) -> None:
        """
        Sets the goal position of the camera.

        The camera will lerp towards this position based on the provided speed,
        updating its position every time the use() function is called.

        :param Vec2 vector: Vector to move the camera towards.
        :param Vec2 speed: How fast to move the camera, 1.0 is instant, 0.1 moves slowly
        """
        pos = Vec2(vector[0], vector[1])
        self.goal_position = pos
        self.move_speed = speed
        self.moving = True

    def move(self, vector: Vec2) -> None:
        """
        Moves the camera with a speed of 1.0, aka instant move

        This is equivalent to calling move_to(my_pos, 1.0)
        """
        self.move_to(vector, 1.0)

    def update(self):
        """
        Update the camera's viewport to the current settings.
        """
        if self.moving:
            # Apply Goal Position
            self.position = self.position.lerp(self.goal_position, self.move_speed)
            if self.position == self.goal_position:
                self.moving = False
            self._set_view_matrix()  # this will alse set the combined matrix

    def use(self):
        self._window.current_camera = self

        # update camera position and calculate matrix values
        self.update()

        self._window.ctx.viewport = self._viewport
        self._window.ctx.projection_2d_matrix = self._combined_matrix


class Camera:
    """
    The Camera class is used for controlling the visible viewport.
    It is very useful for separating a scrolling screen of sprites, and a GUI overlay.
    For an example of this in action, see :ref:`sprite_move_scrolling`.

    :param int viewport_width: Width of the viewport. If not set the window width will be used.
    :param int viewport_height: Height of the viewport. If not set the window height will be used.
    :param Window window: Window to associate with this camera, if working with a multi-window program.

    """

    def __init__(
            self,
            viewport_width: int = 0,
            viewport_height: int = 0,
            window: Optional["arcade.Window"] = None,
    ):
        # Reference to Context, used to update projection matrix
        self._window = window or arcade.get_window()

        # Position
        self.position = Vec2(0, 0)
        self.goal_position = Vec2(0, 0)

        self._rotation = 0.0
        self._anchor: Optional[Tuple[float, float]] = None

        # Movement Speed, 1.0 is instant
        self.move_speed = 1.0

        # Matrixes
        # Projection Matrix is used to apply the camera viewport size
        self.projection_matrix = None
        # View Matrix is what the camera is looking at(position)
        self.view_matrix = None
        # We multiple projection and view matrices to get combined, this is what actually gets sent to GL context
        self.combined_matrix = None

        # Near and Far
        self.near = -1
        self.far = 1

        # Shake
        self.shake_velocity = Vec2()
        self.shake_offset = Vec2()
        self.shake_speed = 0.0
        self.shake_damping = 0.0

        self.scale = 1.0

        self.viewport_width = viewport_width or self._window.width
        self.viewport_height = viewport_height or self._window.height
        self.set_projection()

    @property
    def rotation(self) -> float:
        """
        Get or set the rotation in degrees.

        This will rotate the camera clockwise meaning
        the contents will rotate counter-clockwise.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: float):
        self._rotation = value

    @property
    def anchor(self) -> Optional[Tuple[float, float]]:
        """
        Get or set the rotation anchor for the camera.

        By default, the anchor is the center of the screen
        and the anchor value is `None`. Assigning a custom
        anchor point will override this behavior.
        The anchor point is in world / global coordinates.

        Example::

            # Set the anchor to the center of the world
            camera.anchor = 0, 0
            # Set the anchor to the center of the player
            camera.anchor = player.position
        """
        return self._anchor

    @anchor.setter
    def anchor(self, anchor: Optional[Tuple[float, float]]):
        self._anchor = None if anchor is None else (anchor[0], anchor[1])

    def update(self):
        """
        Update the camera's viewport to the current settings.
        """
        # Apply Goal Position
        self.position = self.position.lerp(self.goal_position, self.move_speed)

        # Apply Camera Shake

        # Move our offset based on shake velocity
        self.shake_offset += self.shake_velocity

        # Get x and ys
        vx = self.shake_velocity[0]
        vy = self.shake_velocity[1]

        ox = self.shake_offset[0]
        oy = self.shake_offset[1]

        # Calculate the angle our offset is at, and how far out
        angle = math.atan2(ox, oy)
        distance = arcade.get_distance(0, 0, ox, oy)
        velocity_mag = arcade.get_distance(0, 0, vx, vy)

        # Ok, what's the reverse? Pull it back in.
        reverse_speed = min(self.shake_speed, distance)
        opposite_angle = angle + math.pi
        opposite_vector = Vec2(
            math.sin(opposite_angle) * reverse_speed,
            math.cos(opposite_angle) * reverse_speed,
        )

        # Shaking almost done? Zero it out
        if velocity_mag < self.shake_speed and distance < self.shake_speed:
            self.shake_velocity = Vec2(0, 0)
            self.shake_offset = Vec2(0, 0)

        # Come up with a new velocity, pulled by opposite vector and damped
        self.shake_velocity += opposite_vector
        self.shake_velocity *= Vec2(self.shake_damping, self.shake_damping)

        # Figure out our 'real' position plus the shake
        result_position = self.position + self.shake_offset
        result_position = Vec3(
            (result_position[0] / ((self.viewport_width * self.scale) / 2)),
            (result_position[1] / ((self.viewport_height * self.scale) / 2)),
            0
        )

        self.view_matrix = ~(Mat4.from_translation(result_position) @ Mat4().scale(Vec3(self.scale, self.scale, 1.0)))
        self.combined_matrix = self.projection_matrix @ self.view_matrix

    def set_projection(self):
        """
        Update the projection matrix of the camera. This creates an orthogonal
        projection based on the viewport size of the camera.
        """
        self.projection_matrix = Mat4.orthogonal_projection(
            0,
            self.scale * self.viewport_width,
            0,
            self.scale * self.viewport_height,
            self.near,
            self.far
        )

    def resize(self, viewport_width: int, viewport_height: int):
        """
        Resize the camera's viewport. Call this when the window resizes.

        :param int viewport_width: Width of the viewport
        :param int viewport_height: Height of the viewport

        """

        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.set_projection()

    def shake(self, velocity: Vec2, speed: float = 1.5, damping: float = 0.9):
        """
        Add a camera shake.

        :param Vec2 velocity: Vector to start moving the camera
        :param float speed: How fast to shake
        :param float damping: How fast to stop shaking
        """
        if not isinstance(velocity, Vec2):
            velocity = Vec2(*velocity)

        self.shake_velocity += velocity
        self.shake_speed = speed
        self.shake_damping = damping

    def move_to(self, vector: Vec2, speed: float = 1.0):
        """
        Sets the goal position of the camera.

        The camera will lerp towards this position based on the provided speed,
        updating its position every time the use() function is called.

        :param Vec2 vector: Vector to move the camera towards.
        :param Vec2 speed: How fast to move the camera, 1.0 is instant, 0.1 moves slowly
        """
        self.goal_position = Vec2(*vector)
        self.move_speed = speed

    def move(self, vector: Vec2):
        """
        Moves the camera with a speed of 1.0, aka instant move

        This is equivalent to calling move_to(my_pos, 1.0)
        """
        self.move_to(vector, 1.0)

    def zoom(self, change: float):
        """
        Zoom the camera in or out. Or not.
        This will currently raise an error
        TODO implement
        """
        raise NotImplementedError(
            "Zooming the camera is currently un-supported, but will be in a later release.")

    def use(self):
        """
        Select this camera for use. Do this right before you draw.
        """
        self._window.current_camera = self

        self.update()
        # Viewport / projection
        self._window.ctx.viewport = 0, 0, int(self.viewport_width), int(
            self.viewport_height)
        self._window.ctx.projection_2d_matrix = self.combined_matrix

        # View matrix for rotation
        rotate = Mat4.from_rotation(math.radians(self._rotation), Vec3(0, 0, 1))

        # If no anchor is set, use the center of the screen
        if self._anchor is None:
            offset = Vec3(self.position.x, self.position.y, 0)
            offset += Vec3(self.viewport_width / 2, self.viewport_height / 2, 0)
        else:
            offset = Vec3(self._anchor[0], self._anchor[1], 0)

        translate_pre = Mat4.from_translation(offset)
        translate_post = Mat4.from_translation(-offset)
        self._window.ctx.view_matrix_2d = translate_post @ rotate @ translate_pre


class AdvanceCamera:
    """
    The Camera class is used for controlling the visible viewport, zoom and rotation.
    It is very useful for separating a scrolling screen of sprites, and a GUI overlay.
    For an example of this in action, see :ref:`sprite_move_scrolling`.

    :param tuple viewport: (left, bottom, width, height) size of the viewport. If None the window size will be used.
    :param tuple projection: (left, right, bottom, top) size of the projection. If None the window size will be used.
    :param float zoom: the zoom to apply to the projection
    :param float rotation: the angle in degrees to rotate the projection
    :param tuple anchor: the x, y point where the camera rotation will anchor. Default is the center of the viewport.
    :param Window window: Window to associate with this camera, if working with a multi-window program.
    """

    def __init__(
            self,
            viewport: Optional[FourIntTuple] = None,
            projection: Optional[FourFloatTuple] = None,
            zoom: float = 1.0,
            rotation: float = 0.0,
            anchor: Optional[Tuple[float, float]] = None,
            window: Optional["arcade.Window"] = None,
    ):
        # Reference to Context, used to update projection matrix
        self._window: "arcade.Window" = window or arcade.get_window()

        # Position
        self.position: Vec2 = Vec2(0, 0)

        # Camera movement
        self.goal_position: Vec2 = Vec2(0, 0)
        self.move_speed: float = 1.0  # 1.0 is instant
        self.moving: bool = False

        self._zoom: float = zoom

        # Rotation
        self._rotation: float = rotation  # in degrees
        self._anchor: Optional[Tuple[float, float]] = anchor  # (x, y) to anchor the camera rotation

        # Near and Far
        self._near: int = -1
        self._far: int = 1

        # Shake
        self.shake_velocity: Vec2 = Vec2()
        self.shake_offset: Vec2 = Vec2()
        self.shake_speed: float = 0.0
        self.shake_damping: float = 0.0
        self.shaking: bool = False

        # viewport is the space the camera will hold on the screen (left, bottom, width, height)
        self._viewport: FourIntTuple = viewport or (0, 0, self._window.width, self._window.height)
        # projection is what you want to project into the camera viewport (left, right, bottom, top)
        self._projection: FourFloatTuple = projection or (0, self._window.width, 0, self._window.height)

        # Matrixes
        # Projection Matrix is used to apply the camera viewport size
        self._projection_matrix: Mat4 = Mat4()
        # View Matrix is what the camera is looking at(position)
        self._view_matrix: Mat4 = Mat4()
        # We multiply projection and view matrices to get combined, this is what actually gets sent to GL context
        self._combined_matrix: Mat4 = Mat4()
        # Rotation matrix holds the matrix used to compute the rotation set in window.ctx.view_matrix_2d
        self._rotation_matrix: Mat4 = Mat4()

        # Init matrixes
        # This will precompute the projection, view, combined and rotation matrixes
        self._set_projection_matrix(update_combined_matrix=False)
        self._set_view_matrix()
        self._set_rotation_matrix()

    @property
    def viewport_width(self) -> int:
        """ Returns the width of the viewport """
        return self._viewport[2]

    @property
    def viewport_height(self) -> int:
        """ Returns the height of the viewport """
        return self._viewport[3]

    @property
    def viewport(self) -> FourIntTuple:
        """ The space the camera will hold on the screen """
        return self._viewport

    @viewport.setter
    def viewport(self, viewport: FourIntTuple) -> None:
        self._viewport = viewport or (0, 0, self._window.width, self._window.height)

        # the viewport could potentially affect the view and the rotation matrix
        self._set_view_matrix()
        self._set_rotation_matrix()

    def _set_projection_matrix(self, *, update_combined_matrix: bool = True) -> None:
        """
        Helper method. This will just precompute the projection and combined matrix

        :param bool update_combined_matrix: if True will also update the combined matrix (projection @ view)
        """
        left, right, bottom, top = self._projection
        if self._zoom != 1.0:
            right *= self._zoom
            top *= self._zoom
        self._projection_matrix = Mat4.orthogonal_projection(left, right, bottom, top, self._near, self._far)
        if update_combined_matrix:
            self._set_combined_matrix()

    def _set_view_matrix(self) -> None:
        """ Helper method. This will just precompute the view and combined matrix"""

        # Figure out our 'real' position plus the shake
        result_position = self.position + self.shake_offset
        result_position = Vec3(
            (result_position[0] / ((self._viewport[2] * self._zoom) / 2)),
            (result_position[1] / ((self._viewport[3] * self._zoom) / 2)),
            0
        )
        self._view_matrix = ~(Mat4.from_translation(result_position) @ Mat4().scale(Vec3(self._zoom, self._zoom, 1.0)))
        self._set_combined_matrix()

    def _set_combined_matrix(self) -> None:
        """ Helper method. This will just precompute the combined matrix"""
        self._combined_matrix = self._projection_matrix @ self._view_matrix

    def _set_rotation_matrix(self) -> None:
        """ Helper method that computes the rotation_matrix every time is needed instead in every frame """
        rotate = Mat4.from_rotation(math.radians(self._rotation), Vec3(0, 0, 1))

        # If no anchor is set, use the center of the screen
        if self._anchor is None:
            offset = Vec3(self.position.x, self.position.y, 0)
            offset += Vec3(self.viewport_width / 2, self.viewport_height / 2, 0)
        else:
            offset = Vec3(self._anchor[0], self._anchor[1], 0)

        translate_pre = Mat4.from_translation(offset)
        translate_post = Mat4.from_translation(-offset)

        self._rotation_matrix = translate_post @ rotate @ translate_pre

    @property
    def projection(self) -> FourFloatTuple:
        """ The dimensions of the space to project in the camera viewport"""
        return self._projection

    @projection.setter
    def projection(self, new_projection: FourFloatTuple) -> None:
        """
        Update the projection of the camera. This also updates the projection matrix with an orthogonal
        projection based on the projection size of the camera and the zoom applied.
        """
        self._projection = new_projection or (0, self._window.width, 0, self._window.height)
        self._set_projection_matrix()

    @property
    def zoom(self) -> float:
        """ The zoom applied to the projection"""
        return self._zoom

    @zoom.setter
    def zoom(self, zoom: float) -> None:
        """
        Update the zoom of the camera. This also updates the projection matrix with an orthogonal
        projection based on the projection size of the camera and the zoom applied.
        """
        self._zoom = zoom

        # Changing the zoom affects both projection_matrix and view_matrix
        self._set_projection_matrix(update_combined_matrix=False)  # combined matrix will be set in the next call
        self._set_view_matrix()

    @property
    def near(self) -> int:
        """ The near applied to the projection"""
        return self._near

    @near.setter
    def near(self, near: int) -> None:
        """
        Update the near of the camera. This also updates the projection matrix with an orthogonal
        projection based on the projection size of the camera and the zoom applied.
        """
        self._near = near
        self._set_projection_matrix()

    @property
    def far(self) -> int:
        """ The far applied to the projection"""
        return self._far

    @far.setter
    def far(self, far: int) -> None:
        """
        Update the far of the camera. This also updates the projection matrix with an orthogonal
        projection based on the projection size of the camera and the zoom applied.
        """
        self._far = far
        self._set_projection_matrix()

    @property
    def rotation(self) -> float:
        """
        Get or set the rotation in degrees.

        This will rotate the camera clockwise meaning
        the contents will rotate counter-clockwise.
        """
        return self._rotation

    @rotation.setter
    def rotation(self, value: float) -> None:
        self._rotation = value
        self._set_rotation_matrix()

    @property
    def anchor(self) -> Optional[Tuple[float, float]]:
        """
        Get or set the rotation anchor for the camera.

        By default, the anchor is the center of the screen
        and the anchor value is `None`. Assigning a custom
        anchor point will override this behavior.
        The anchor point is in world / global coordinates.

        Example::

            # Set the anchor to the center of the world
            camera.anchor = 0, 0
            # Set the anchor to the center of the player
            camera.anchor = player.position
        """
        return self._anchor

    @anchor.setter
    def anchor(self, anchor: Optional[Tuple[float, float]]) -> None:
        if anchor is None:
            self._anchor = None
        else:
            self._anchor = anchor[0], anchor[1]
        self._set_rotation_matrix()

    def update(self) -> None:
        """
        Update the camera's viewport to the current settings.
        """
        if self.moving:
            # Apply Goal Position
            self.position = self.position.lerp(self.goal_position, self.move_speed)
            if self.position == self.goal_position:
                self.moving = False

        if self.shaking:
            # Apply Camera Shake

            # Move our offset based on shake velocity
            self.shake_offset += self.shake_velocity

            # Get x and ys
            vx = self.shake_velocity[0]
            vy = self.shake_velocity[1]

            ox = self.shake_offset[0]
            oy = self.shake_offset[1]

            # Calculate the angle our offset is at, and how far out
            angle = math.atan2(ox, oy)
            distance = arcade.get_distance(0, 0, ox, oy)
            velocity_mag = arcade.get_distance(0, 0, vx, vy)

            # Ok, what's the reverse? Pull it back in.
            reverse_speed = min(self.shake_speed, distance)
            opposite_angle = angle + math.pi
            opposite_vector = Vec2(
                math.sin(opposite_angle) * reverse_speed,
                math.cos(opposite_angle) * reverse_speed,
            )

            # Shaking almost done? Zero it out
            if velocity_mag < self.shake_speed and distance < self.shake_speed:
                self.shake_velocity = Vec2(0, 0)
                self.shake_offset = Vec2(0, 0)
                self.shaking = False

            # Come up with a new velocity, pulled by opposite vector and damped
            self.shake_velocity += opposite_vector
            self.shake_velocity *= Vec2(self.shake_damping, self.shake_damping)

        if self.moving or self.shaking:
            self._set_view_matrix()  # this will also set the combined matrix

    def resize(self, viewport_width: int, viewport_height: int) -> None:
        """
        Resize the camera's viewport. Call this when the window resizes.

        :param int viewport_width: Width of the viewport
        :param int viewport_height: Height of the viewport

        """
        self.viewport = (self._viewport[0], self._viewport[1], viewport_width, viewport_height)

    def shake(self, velocity: Vec2, speed: float = 1.5, damping: float = 0.9) -> None:
        """
        Add a camera shake.

        :param Vec2 velocity: Vector to start moving the camera
        :param float speed: How fast to shake
        :param float damping: How fast to stop shaking
        """
        if not isinstance(velocity, Vec2):
            velocity = Vec2(*velocity)

        self.shake_velocity += velocity
        self.shake_speed = speed
        self.shake_damping = damping
        self.shaking = True

    def move_to(self, vector: Union[Vec2, tuple], speed: float = 1.0) -> None:
        """
        Sets the goal position of the camera.

        The camera will lerp towards this position based on the provided speed,
        updating its position every time the use() function is called.

        :param Vec2 vector: Vector to move the camera towards.
        :param Vec2 speed: How fast to move the camera, 1.0 is instant, 0.1 moves slowly
        """
        self.goal_position = Vec2(*vector)
        self.move_speed = speed
        self.moving = True

    def move(self, vector: Union[Vec2, tuple]) -> None:
        """
        Moves the camera with a speed of 1.0, aka instant move

        This is equivalent to calling move_to(my_pos, 1.0)
        """
        self.move_to(vector, 1.0)

    def center(self, vector: Union[Vec2, tuple], speed: float = 1.0) -> None:
        """
        Centers the camera on coordinates
        """
        position = self.position

        if not isinstance(vector, Vec2):
            vector = Vec2(*vector)
        if not isinstance(position, Vec2):
            position = Vec2(*position)

        center = Vec2(self.viewport_width / 2, self.viewport_height / 2)

        target = vector + position - center

        self.move_to(target, speed)

    def get_map_coordinates(self, camera_vector: Union[Vec2, tuple]) -> Vec2:
        """
        Returns map coordinates in pixels from screen coordinates based on the camera position

        :param Vec2 camera_vector: Vector captured from the camera viewport
        """
        return Vec2(*self.position) + Vec2(*camera_vector)

    def use(self) -> None:
        """
        Select this camera for use. Do this right before you draw.
        """
        self._window.current_camera = self

        # update camera position and calculate matrix values if needed
        self.update()

        # set Viewport / projection / rotation matrixes
        self._window.ctx.viewport = self._viewport  # sets viewport of the camera
        self._window.ctx.projection_2d_matrix = self._combined_matrix  # sets projection position and zoom
        self._window.ctx.view_matrix_2d = self._rotation_matrix  # sets rotation and rotation anchor
