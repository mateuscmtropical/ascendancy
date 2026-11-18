"""Facial shape keys for the assembled characters (blink, lids, brows, mouth, gaze).

The base heads come without face bones or shape keys, so the expressions are sculpted here by code: the eye
opening of each head is measured by casting rays from the eyeball centre, the lids slide over the eyeball along
its sphere, and brows and mouth move by smooth displacement fields around landmarks measured on the mesh.
features/player/face_animator.gd drives the exported blend shapes by name.
"""

import itertools
import math

import bmesh
import numpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

LID_REACH = 2.1  # the lids are the head vertices within this many eyeball radii of the eye centre
LID_INNER_REACH = 0.85  # closer to the eye centre than this is socket wall, not lid
SCAN_START = 0.55  # eyeball radii from the eye centre where the rays that look for the opening start
LID_CLEARANCE = 0.0009  # metres a closed lid stays in front of the eyeball
LID_FOLLOW = math.radians(34.0)  # skin above/below the lid edge that stretches with it
LID_MEETING = 0.14  # where the lids meet, as a fraction of the opening counted from the lower lid
CORNER_FADE = math.radians(10.0)
SPHERE_FIT_PASSES = 4
SPHERE_FIT_TOLERANCE = 0.0008
SCAN_AZIMUTHS = numpy.radians(numpy.arange(-80.0, 81.0, 2.0))
SCAN_ELEVATIONS = numpy.radians(numpy.arange(-50.0, 51.0, 1.0))
GAZE_YAW = math.radians(16.0)
GAZE_PITCH = math.radians(11.0)
BROW_SKIN_BAND = 0.013  # metres of skin above and below the brow line that follow the brow
MOUTH_CORNER_REACH = 0.017
JAW_DROP = math.radians(11.0)
MOUTH_SEARCH = (0.045, 0.05, 0.105)  # half width, and nearest/farthest drop below the eyes, of the lip seam
MOUTH_FALLBACK = (0.076, 0.026)  # drop below the eyes and half width when the lip seam is not found

# name: (upper lid, lower lid) travel towards the meeting line; 1 closes, negative opens wider
LID_POSES = {"blink": (1.0, 1.0), "squint": (0.38, 0.75), "eyes_wide": (-0.42, -0.25)}
# name: (inner end, outer end) lift of the brow in metres, and how far the inner end slides to the nose
BROW_POSES = {"brow_up": (0.0065, 0.005, 0.0), "brow_angry": (-0.0065, 0.0015, 0.0025), "brow_sad": (0.006, -0.003, -0.001)}
# name: corner displacement (outwards, backwards, up) in metres and the lift of the cheeks
MOUTH_POSES = {"smile": ((0.0045, 0.003, 0.006), 0.0028), "frown": ((-0.001, 0.001, -0.0055), -0.001)}


def smoothstep(value: float) -> float:
    clamped = min(1.0, max(0.0, value))

    return clamped * clamped * (3.0 - 2.0 * clamped)


def world_positions(mesh_object) -> list:
    return [mesh_object.matrix_world @ vertex.co for vertex in mesh_object.data.vertices]


def add_shape(mesh_object, name: str, moved: dict) -> None:
    """Shape key from {vertex index: world position}; the untouched vertices keep the basis."""
    to_local = mesh_object.matrix_world.inverted()

    if mesh_object.data.shape_keys is None:
        mesh_object.shape_key_add(name="Basis", from_mix=False)

    key = mesh_object.shape_key_add(name=name, from_mix=False)

    for index, position in moved.items():
        key.data[index].co = to_local @ position


def fit_sphere(points: list) -> tuple:
    """Centre and radius of the sphere through most of the points; lashes and the cornea bulge that sit off the
    eyeball are dropped between passes."""
    kept = numpy.array([tuple(point) for point in points])

    for _ in range(SPHERE_FIT_PASSES):
        system = numpy.hstack((2.0 * kept, numpy.ones((len(kept), 1))))
        solution = numpy.linalg.lstsq(system, (kept ** 2).sum(axis=1), rcond=None)[0]
        centre = solution[:3]
        radius = math.sqrt(solution[3] + (centre ** 2).sum())
        off_sphere = numpy.abs(numpy.linalg.norm(kept - centre, axis=1) - radius)
        kept = kept[off_sphere <= max(SPHERE_FIT_TOLERANCE, numpy.median(off_sphere) * 2.0)]

    return Vector(centre), radius


def largest_region(mask: numpy.ndarray) -> numpy.ndarray:
    """The mask with only its biggest connected patch: rays also slip through small gaps beside the nose."""
    remaining = {tuple(cell) for cell in numpy.argwhere(mask)}
    biggest = set()

    while remaining:
        frontier = [remaining.pop()]
        region = set(frontier)

        while frontier:
            column, row = frontier.pop()
            neighbours = {(column + 1, row), (column - 1, row), (column, row + 1), (column, row - 1)} & remaining

            remaining -= neighbours
            region |= neighbours
            frontier += neighbours

        biggest = max(biggest, region, key=len)

    kept = numpy.zeros_like(mask)

    for cell in biggest:
        kept[cell] = True

    return kept


class Eye:
    """One eyeball as a sphere, with the opening of the lids around it measured in angles from its centre:
    azimuth grows towards the temple, elevation upwards."""

    def __init__(self, eye_points: list, side: float, head_tree: BVHTree, eye_tree: BVHTree) -> None:
        self.side = side
        self.centre, self.radius = fit_sphere(eye_points)
        self.eye_tree = eye_tree
        self.measure_opening(head_tree)

    def direction(self, azimuth: float, elevation: float) -> Vector:
        return Vector((math.sin(azimuth) * math.cos(elevation) * self.side, -math.cos(azimuth) * math.cos(elevation), math.sin(elevation)))

    def angles(self, point: Vector) -> tuple:
        offset = point - self.centre
        distance = offset.length

        return math.atan2(offset.x * self.side, -offset.y), math.asin(max(-1.0, min(1.0, offset.z / distance))), distance

    def measure_opening(self, head_tree: BVHTree) -> None:
        is_open = numpy.array([
            self.is_open(head_tree, self.direction(azimuth, elevation))
            for azimuth, elevation in itertools.product(SCAN_AZIMUTHS, SCAN_ELEVATIONS)
        ]).reshape(len(SCAN_AZIMUTHS), len(SCAN_ELEVATIONS))
        is_open = largest_region(is_open)
        columns = [index for index in range(len(SCAN_AZIMUTHS)) if is_open[index].sum() >= 2]

        self.azimuths = SCAN_AZIMUTHS[columns]
        self.lower = numpy.array([SCAN_ELEVATIONS[is_open[index]].min() for index in columns])
        self.upper = numpy.array([SCAN_ELEVATIONS[is_open[index]].max() for index in columns])

    def is_open(self, head_tree: BVHTree, direction: Vector) -> bool:
        """True when nothing of the head covers the eyeball in this direction. The ray starts part of the way
        out because some heads have their socket wall inside the eyeball."""
        start = self.centre + direction * self.radius * SCAN_START

        return head_tree.ray_cast(start, direction, self.radius * 2.0)[0] is None

    def opening_at(self, azimuth: float) -> tuple:
        return float(numpy.interp(azimuth, self.azimuths, self.lower)), float(numpy.interp(azimuth, self.azimuths, self.upper))

    def corner_weight(self, azimuth: float) -> float:
        outside = max(self.azimuths[0] - azimuth, azimuth - self.azimuths[-1], 0.0)

        return 1.0 - smoothstep(outside / CORNER_FADE)

    def lid_position(self, point: Vector, upper_travel: float, lower_travel: float) -> Vector:
        """Where a lid vertex goes when the upper and lower lid edges travel towards the meeting line."""
        azimuth, elevation, distance = self.angles(point)
        lower, upper = self.opening_at(azimuth)
        meeting = lower + (upper - lower) * LID_MEETING
        is_upper_lid = elevation >= (lower + upper) / 2.0
        edge, travel, limit = (upper, upper_travel, upper + LID_FOLLOW) if is_upper_lid else (lower, lower_travel, lower - LID_FOLLOW)
        edge_target = edge + (meeting - edge) * travel
        # skin between the edge and the limit stretches linearly; the fold behind the edge rides with the edge
        stretch = min(1.0, max(0.0, (elevation - limit) / (edge - limit)))
        new_elevation = limit + (edge_target - limit) * stretch
        direction = self.direction(azimuth, new_elevation)
        eyeball_hit = self.eye_tree.ray_cast(self.centre, direction, self.radius * 2.0)[0]
        eyeball_distance = (eyeball_hit - self.centre).length if eyeball_hit else self.radius
        moved = self.centre + direction * max(distance, eyeball_distance + LID_CLEARANCE)

        return point.lerp(moved, self.corner_weight(azimuth))

    def lid_vertices(self, head_points: list) -> list:
        return [
            index for index, point in enumerate(head_points)
            if point.y < self.centre.y + self.radius * 0.4 and self.radius * LID_INNER_REACH < (point - self.centre).length < self.radius * LID_REACH
        ]


def mesh_tree(mesh_object) -> BVHTree:
    polygons = [tuple(polygon.vertices) for polygon in mesh_object.data.polygons]

    return BVHTree.FromPolygons(world_positions(mesh_object), polygons)


def find_eyes(head, eyes_object) -> list:
    eye_points = world_positions(eyes_object)
    head_tree, eye_tree = mesh_tree(head), mesh_tree(eyes_object)

    return [Eye([point for point in eye_points if point.x * side > 0.0], side, head_tree, eye_tree) for side in (1.0, -1.0)]


def add_lid_shapes(head, eyes: list) -> None:
    head_points = world_positions(head)
    lids = [(eye, eye.lid_vertices(head_points)) for eye in eyes]

    for name, (upper_travel, lower_travel) in LID_POSES.items():
        per_eye = [{index: eye.lid_position(head_points[index], upper_travel, lower_travel) for index in indices} for eye, indices in lids]

        if name == "blink":
            add_shape(head, "blink_l", per_eye[0])
            add_shape(head, "blink_r", per_eye[1])
            continue

        add_shape(head, name, {**per_eye[0], **per_eye[1]})


def add_gaze_shapes(eyes_object, eyes: list) -> None:
    eye_points = world_positions(eyes_object)
    turns = {
        "look_left": Matrix.Rotation(GAZE_YAW, 4, "Z"), "look_right": Matrix.Rotation(-GAZE_YAW, 4, "Z"),
        "look_up": Matrix.Rotation(GAZE_PITCH, 4, "X"), "look_down": Matrix.Rotation(-GAZE_PITCH, 4, "X"),
    }
    centre_by_side = {eye.side: eye.centre for eye in eyes}

    for name, turn in turns.items():
        moved = {}

        for index, point in enumerate(eye_points):
            centre = centre_by_side[1.0 if point.x > 0.0 else -1.0]
            moved[index] = centre + turn @ (point - centre)

        add_shape(eyes_object, name, moved)


def brow_offset(point: Vector, brow_span: tuple, pose: tuple) -> Vector:
    inner_lift, outer_lift, slide = pose
    inner_x, outer_x = brow_span
    along = min(1.0, max(0.0, (abs(point.x) - inner_x) / (outer_x - inner_x)))
    side = 1.0 if point.x > 0.0 else -1.0

    return Vector((-side * slide * (1.0 - along), 0.0, inner_lift + (outer_lift - inner_lift) * along))


def add_brow_shapes(head, eyebrows) -> None:
    brow_points = world_positions(eyebrows)
    head_points = world_positions(head)
    brow_span = (min(abs(point.x) for point in brow_points), max(abs(point.x) for point in brow_points))
    brow_height = sum(point.z for point in brow_points) / len(brow_points)
    front = max(point.y for point in brow_points) + 0.02
    # skin weight: full on the brow line, fading over the band above and below and past the outer end
    skin = {
        index: math.exp(-((point.z - brow_height) / BROW_SKIN_BAND) ** 2) * (1.0 - smoothstep((abs(point.x) - brow_span[1]) / 0.012))
        for index, point in enumerate(head_points) if point.y < front and abs(point.z - brow_height) < BROW_SKIN_BAND * 2.2
    }

    for name, pose in BROW_POSES.items():
        add_shape(eyebrows, name, {index: point + brow_offset(point, brow_span, pose) for index, point in enumerate(brow_points)})
        add_shape(head, name, {index: head_points[index] + brow_offset(head_points[index], brow_span, pose) * weight for index, weight in skin.items()})


class Mouth:
    """The lip line: found as the seam the head mesh has between the lips, below the eyes."""

    def __init__(self, head, eyes: list) -> None:
        eye_height = eyes[0].centre.z
        half_width, nearest, farthest = MOUTH_SEARCH
        mesh = bmesh.new()

        mesh.from_mesh(head.data)

        seam = [
            head.matrix_world @ vertex.co for vertex in mesh.verts
            if vertex.is_boundary and abs(vertex.co.x) < half_width
        ]
        seam = [point for point in seam if eye_height - farthest < point.z < eye_height - nearest and point.y < eyes[0].centre.y]
        mesh.free()

        self.found = len(seam) >= 8
        self.height = sum(point.z for point in seam) / len(seam) if self.found else eye_height - MOUTH_FALLBACK[0]
        self.seam = sorted((abs(point.x), point.z) for point in seam) or [(0.0, self.height)]
        self.half_width = max(abs(point.x) for point in seam) if self.found else MOUTH_FALLBACK[1]
        self.points = world_positions(head)
        front_points = [point for point in self.points if abs(point.z - self.height) < 0.004 and abs(point.x) < self.half_width]
        self.front = min(point.y for point in front_points)
        self.corner_depth = max(point.y for point in front_points if abs(point.x) > self.half_width * 0.85)
        self.depth = eyes[0].centre.y + eyes[0].radius  # nothing behind the eyeballs belongs to the mouth
        self.lower_side = self.find_lower_side(head)

    def find_lower_side(self, head) -> set:
        """Vertices of the lower lip and jaw: below the lip line, or on it and used only by faces below it."""
        face_heights = {}

        for polygon in head.data.polygons:
            centre = sum((self.points[index] for index in polygon.vertices), Vector()) / len(polygon.vertices)

            for index in polygon.vertices:
                face_heights.setdefault(index, []).append(centre.z)

        return {index for index, heights in face_heights.items() if sum(heights) / len(heights) < self.line_height(self.points[index].x)}

    def line_height(self, x: float) -> float:
        """Height of the gap between the lips at x: the middle of the seam points around it."""
        near = [height for distance, height in self.seam if abs(distance - abs(x)) < 0.004]

        return (min(near) + max(near)) / 2.0 if near else self.height

    def corner(self, side: float) -> Vector:
        return Vector((self.half_width * side, self.corner_depth, self.height))

    def corner_shape(self, pose: tuple) -> dict:
        (outwards, backwards, lift), cheek_lift = pose
        moved = {}

        for index, point in enumerate(self.points):
            if point.y > self.depth:
                continue

            side = 1.0 if point.x >= 0.0 else -1.0
            corner_weight = math.exp(-((point - self.corner(side)).length / MOUTH_CORNER_REACH) ** 2)
            # the lip line bends with the corners: nothing at the centre, full at the corners
            line_weight = min(1.0, abs(point.x) / self.half_width) ** 2 * math.exp(-((point.z - self.height) / 0.007) ** 2)
            cheek_weight = math.exp(-((point - self.corner(side) - Vector((side * 0.012, 0.004, 0.022))).length / 0.02) ** 2)
            weight = max(corner_weight, line_weight * 0.75)
            offset = Vector((side * outwards, backwards, lift)) * weight + Vector((0.0, 0.0, cheek_lift)) * cheek_weight

            if offset.length > 0.00005:
                moved[index] = point + offset

        return moved

    def open_shape(self) -> dict:
        hinge = Vector((0.0, self.depth + 0.055, self.height + 0.03))
        turn = Matrix.Rotation(JAW_DROP, 4, "X")
        moved = {}

        for index, point in enumerate(self.points):
            if point.y > self.depth:
                continue

            # between the corners the lips part along the seam; past the corners the skin is one piece, so the
            # jaw takes hold gradually below the lip line
            parting = 1.0 - smoothstep((abs(point.x) - self.half_width * 0.55) / (self.half_width * 0.45))
            below_line = smoothstep((self.line_height(point.x) - point.z) / 0.016)
            hold = below_line + (1.0 - below_line) * parting if index in self.lower_side else below_line * (1.0 - parting)
            # full on lip and chin, fading out to the sides and down the throat
            weight = hold * (1.0 - smoothstep((abs(point.x) - 0.03) / 0.03)) * (1.0 - smoothstep((self.height - 0.062 - point.z) / 0.02)) * (1.0 - smoothstep((point.y - (self.front + 0.035)) / 0.03))

            if weight > 0.001:
                moved[index] = point.lerp(hinge + turn @ (point - hinge), weight)

        return moved


def add_mouth_shapes(head, eyes: list) -> None:
    mouth = Mouth(head, eyes)

    print(f"  mouth seam found={mouth.found} height={mouth.height:.3f} half_width={mouth.half_width:.3f}")

    for name, pose in MOUTH_POSES.items():
        add_shape(head, name, mouth.corner_shape(pose))

    add_shape(head, "mouth_open", mouth.open_shape())


def add_face_shapes(head, eyes_object, eyebrows) -> None:
    eyes = find_eyes(head, eyes_object)

    for eye in eyes:
        print(f"  eye side={eye.side:+.0f} radius={eye.radius:.4f} opening azimuth {math.degrees(eye.azimuths[0]):.0f}..{math.degrees(eye.azimuths[-1]):.0f} deg, tallest {math.degrees((eye.upper - eye.lower).max()):.0f} deg")

    add_lid_shapes(head, eyes)
    add_gaze_shapes(eyes_object, eyes)
    add_brow_shapes(head, eyebrows)
    add_mouth_shapes(head, eyes)
