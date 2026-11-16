"""Body of the Mula sem cabeça modelled in separate parts (trunk, neck, pectorals, shoulder blades, arms, legs,
croup, thighs), each one a loft of elliptical cross sections along the bone it rides on. mula_body.py fuses the
parts with a fine voxel remesh: the creases where two parts meet stay and read as the gaps between muscles.

Units and axes are the pack horse's (about 3.4 per metre, Z up, head toward -Y), before the generator stretches the
legs and spreads the chest. A section is (centre, half width along X, half depth, bone): the depth runs across the
path inside the YZ plane (front-to-back on a leg, top-to-bottom on the trunk). Parts off the middle plane are
mirrored, and `.L` in a bone name becomes `.R` on the mirror image."""

import math

import numpy
from mathutils import Vector

RING_POINTS = 20
SPAN_STEPS = 4  # rings laid between two sections of the table
BLEND_START, BLEND_REACH = 0.9, 0.5  # a part owns the skin up to 0.9 of its section and lets go over the next half

PARTS = {
    # caixa do tronco: peito estreito na frente (os peitorais vêm por cima), cilha funda, barriga recolhida, garupa
    "trunk": [
        ((0.0, -2.9, 4.3), 0.7, 0.85, "Shoulders"),
        ((0.0, -2.2, 4.3), 1.1, 1.3, "Shoulders"),
        ((0.0, -1.4, 4.3), 1.25, 1.38, "Torso"),
        ((0.0, -0.4, 4.45), 1.3, 1.22, "Torso"),
        ((0.0, 0.6, 4.6), 1.2, 1.02, "Hips"),
        ((0.0, 1.5, 4.65), 1.02, 0.88, "Hips"),
        ((0.0, 2.3, 4.6), 0.82, 0.78, "Back"),
        ((0.0, 2.85, 4.45), 0.42, 0.48, "Back"),
    ],
    "withers": [
        ((0.0, -2.5, 5.45), 0.3, 0.28, "Shoulders"),
        ((0.0, -1.85, 5.62), 0.4, 0.42, "Shoulders"),
        ((0.0, -0.9, 5.4), 0.34, 0.3, "Torso"),
    ],
    # tronco de árvore que sai do peito inclinado e afina até o corte
    "neck": [
        ((0.0, -2.1, 4.6), 1.1, 1.2, "Shoulders"),
        ((0.0, -2.6, 5.3), 1.02, 1.1, "Shoulders"),
        ((0.0, -3.1, 6.1), 0.86, 0.95, "Neck"),
        ((0.0, -3.6, 6.95), 0.7, 0.76, "Neck"),
        ((0.0, -4.15, 7.9), 0.62, 0.66, "Neck"),
    ],
    # peitoral: um globo de cada lado, com o sulco no meio
    "pectoral": [
        ((0.42, -3.15, 4.8), 0.36, 0.38, "Shoulders"),
        ((0.52, -3.35, 4.2), 0.66, 0.7, "Shoulders"),
        ((0.52, -3.15, 3.6), 0.56, 0.58, "Shoulders"),
        ((0.45, -2.6, 3.2), 0.28, 0.3, "Shoulders"),
    ],
    # espádua: placa inclinada sobre as costelas, da cernelha à ponta do ombro
    "shoulder_blade": [
        ((0.92, -1.5, 5.3), 0.3, 0.5, "Shoulders"),
        ((1.08, -1.9, 4.7), 0.5, 0.86, "Shoulders"),
        ((1.2, -2.4, 4.0), 0.56, 0.78, "FrontLeg.L"),
        ((1.15, -2.75, 3.55), 0.46, 0.5, "FrontLeg.L"),
    ],
    # braço e tríceps: da ponta do ombro para trás até o cotovelo, por trás do peitoral
    "arm": [
        ((1.1, -2.6, 3.6), 0.38, 0.45, "FrontLeg.L"),
        ((1.12, -2.0, 3.55), 0.54, 0.74, "FrontLeg.L"),
        ((1.02, -1.5, 3.35), 0.34, 0.5, "FrontLeg.L"),
    ],
    "foreleg": [
        ((0.92, -1.85, 3.45), 0.44, 0.76, "FrontUpLeg.L"),  # cotovelo
        ((0.9, -1.95, 2.9), 0.4, 0.64, "FrontUpLeg.L"),  # antebraço largo em cima
        ((0.88, -2.05, 2.3), 0.3, 0.42, "FrontUpLeg.L"),
        ((0.87, -2.1, 1.95), 0.24, 0.27, "FrontUpLeg.L"),
        ((0.87, -2.12, 1.7), 0.33, 0.37, "FrontLowLeg.L"),  # joelho mais largo que a canela
        ((0.87, -2.08, 1.45), 0.19, 0.22, "FrontLowLeg.L"),
        ((0.87, -2.0, 1.1), 0.15, 0.2, "FrontLowLeg.L"),  # canela estreita e funda
        ((0.87, -1.96, 0.8), 0.16, 0.21, "FrontLowLeg.L"),
        ((0.87, -1.94, 0.66), 0.24, 0.27, "FrontLowLeg.L"),  # boleto
        ((0.87, -2.0, 0.5), 0.19, 0.2, "FrontLowLeg.L"),  # quartela
        ((0.87, -2.08, 0.38), 0.24, 0.27, "FrontFoot.L"),
        ((0.87, -2.16, 0.06), 0.33, 0.38, "FrontFoot.L"),  # casco
    ],
    # garupa: um globo de cada lado
    "croup": [
        ((0.6, 1.2, 5.0), 0.48, 0.5, "Hips"),
        ((0.74, 1.9, 4.8), 0.82, 0.88, "Back"),
        ((0.74, 2.5, 4.4), 0.62, 0.78, "Back"),
    ],
    "thigh": [
        ((0.9, 1.9, 4.5), 0.64, 1.1, "BackLeg.L"),
        ((0.94, 1.95, 3.9), 0.62, 1.05, "BackLeg.L"),
        ((0.88, 2.0, 3.35), 0.42, 0.7, "BackUpLeg.L"),
    ],
    "hindleg": [
        ((0.8, 2.05, 3.3), 0.44, 0.78, "BackUpLeg.L"),  # soldra
        ((0.78, 2.35, 2.9), 0.38, 0.62, "BackUpLeg.L"),  # perna (gaskin) cheia
        ((0.76, 2.65, 2.5), 0.28, 0.42, "BackUpLeg.L"),
        ((0.75, 2.85, 2.25), 0.31, 0.42, "BackLowLeg.L"),  # jarrete
        ((0.75, 2.82, 1.95), 0.2, 0.26, "BackLowLeg.L"),
        ((0.75, 2.74, 1.4), 0.15, 0.2, "BackLowLeg.L"),
        ((0.75, 2.68, 0.8), 0.16, 0.21, "BackLowLeg.L"),
        ((0.75, 2.66, 0.66), 0.24, 0.27, "BackLowLeg.L"),
        ((0.75, 2.6, 0.5), 0.19, 0.2, "BackLowLeg.L"),
        ((0.75, 2.52, 0.38), 0.24, 0.27, "BackFoot.L"),
        ((0.75, 2.44, 0.06), 0.33, 0.38, "BackFoot.L"),
    ],
    "dock": [
        ((0.0, 2.7, 4.85), 0.2, 0.2, "Tail1"),
        ((0.0, 3.15, 4.7), 0.12, 0.12, "Tail1"),
    ],
}


def mirrored_sections(sections: list) -> list:
    """The part and, when it sits off the middle plane, its mirror image (with the bones of the other side)."""
    if all(center[0] == 0.0 for center, _, _, _ in sections):
        return [sections]

    return [sections, [((-center[0], center[1], center[2]), width, depth, bone.replace(".L", ".R")) for center, width, depth, bone in sections]]


def all_parts() -> list:
    return [copy for sections in PARTS.values() for copy in mirrored_sections(sections)]


def rings_of(sections: list) -> list:
    """(centre, half width, half depth, bone shares) of every ring of the loft: the table sections and the rings
    eased between them."""
    rings = []
    last_span = len(sections) - 2

    for span in range(len(sections) - 1):
        (start, start_width, start_depth, start_bone), (end, end_width, end_depth, end_bone) = sections[span], sections[span + 1]
        steps = range(SPAN_STEPS + 1) if span == last_span else range(SPAN_STEPS)

        for step in steps:
            share = step / SPAN_STEPS
            eased = share * share * (3.0 - 2.0 * share)
            bones = {start_bone: 1.0} if start_bone == end_bone else {start_bone: 1.0 - share, end_bone: share}

            rings.append((Vector(start).lerp(Vector(end), share), start_width + (end_width - start_width) * eased,
                          start_depth + (end_depth - start_depth) * eased, bones))

    return rings


def add_loft(clay, sections: list) -> None:
    """Closed skin of one part: an ellipse per ring, across the path, capped with a shrunken ring at each end."""
    rings = rings_of(sections)
    centers = [center for center, _, _, _ in rings]
    loops = []

    for index, (center, width, depth, _) in enumerate(rings):
        tangent = (centers[min(index + 1, len(rings) - 1)] - centers[max(index - 1, 0)]).normalized()
        across = tangent.cross(Vector((1.0, 0.0, 0.0))).normalized()

        loops.append([clay.verts.new(center + Vector((width * math.cos(angle), 0.0, 0.0)) + across * (depth * math.sin(angle)))
                      for angle in [2.0 * math.pi * point / RING_POINTS for point in range(RING_POINTS)]])

    for near, far in zip(loops, loops[1:]):
        for point in range(RING_POINTS):
            clay.faces.new((near[point], near[(point + 1) % RING_POINTS], far[(point + 1) % RING_POINTS], far[point]))

    clay.faces.new(loops[0][::-1])
    clay.faces.new(loops[-1])


def trunk_section(y: float) -> tuple:
    """(centre Z, half width, half depth) of the trunk box at a given Y, for the relief laid on it."""
    sections = PARTS["trunk"]

    for (start, start_width, start_depth, _), (end, end_width, end_depth, _) in zip(sections, sections[1:]):
        if start[1] <= y <= end[1]:
            share = (y - start[1]) / (end[1] - start[1])

            return (start[2] + (end[2] - start[2]) * share, start_width + (end_width - start_width) * share,
                    start_depth + (end_depth - start_depth) * share)

    raise ValueError(f"Y {y} is outside the trunk")


def part_influences(positions: numpy.ndarray, sections: list) -> tuple:
    """How much one part owns each point (1 inside its section, fading to 0 just outside) and the bone shares of
    the ring nearest to the point."""
    rings = rings_of(sections)
    reach = numpy.empty((len(rings), len(positions)))

    for index, (center, width, depth, _) in enumerate(rings):
        offset = positions - numpy.array(center)
        reach[index] = numpy.hypot(offset[:, 0] / width, numpy.hypot(offset[:, 1], offset[:, 2]) / depth)

    nearest = reach.argmin(axis=0)
    distance = reach.min(axis=0)
    hold = numpy.clip(1.0 - (distance - BLEND_START) / BLEND_REACH, 0.0, 1.0)

    return hold, distance, [rings[index][3] for index in nearest]


def paint_weights(body, bone_names: list) -> None:
    """Each part weighs on its own bones; parts only mix where they overlap (the joints), so a leg bends without
    dragging the chest. A point no part reaches (hanging tatters) goes with the nearest part."""
    positions = numpy.array([vertex.co[:] for vertex in body.data.vertices])
    groups = {name: body.vertex_groups.new(name=name) for name in bone_names}
    influences = [part_influences(positions, sections) for sections in all_parts()]
    holds = numpy.array([hold for hold, _, _ in influences])
    distances = numpy.array([distance for _, distance, _ in influences])
    orphans = holds.sum(axis=0) == 0.0
    holds[distances.argmin(axis=0)[orphans], numpy.nonzero(orphans)[0]] = 1.0
    holds /= holds.sum(axis=0)

    for vertex_index in range(len(positions)):
        blended = {}

        for part_index in numpy.nonzero(holds[:, vertex_index] > 0.01)[0]:
            for bone, share in influences[part_index][2][vertex_index].items():
                blended[bone] = blended.get(bone, 0.0) + share * holds[part_index, vertex_index]

        total = sum(blended.values())

        for bone, weight in blended.items():
            if bone not in groups:
                groups[bone] = body.vertex_groups.new(name=bone)

            groups[bone].add([vertex_index], weight / total, "REPLACE")
