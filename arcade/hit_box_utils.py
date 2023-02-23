import typing
import glm
from glm import array as glm_array, vec2 as glm_vec2

from arcade.types import PointList

if typing.TYPE_CHECKING:
    FastPointList = glm_array[glm.vec2]
else:
    FastPointList = None

def points_to_fast_points(points: PointList) -> FastPointList:
    return glm_array([glm_vec2(point) for point in points])

def fast_points_to_points(points: FastPointList) -> PointList:
    return [(x, y) for x, y in points]