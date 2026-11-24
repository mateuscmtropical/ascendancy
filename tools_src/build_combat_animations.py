"""Unarmed combat clips (guard idle, kicks, uppercut, hook) authored by code on the 65-bone Universal rig.

The CC0 animation libraries bring a jab and a cross but no kicks. Each clip here is a short table of key poses
written in body terms (where the hips, hands and feet are, how the trunk turns and leans); every channel is
interpolated with its own spline, limbs are solved with two-bone IK and the result is baked to bone keys.
All clips start and end in the guard of the library's Punch_Jab, so they chain with it without a pop; the seated
clips of the couple on the plaza bench (SEATED_CLIPS) start from the library's Sitting_Idle instead.

Usage:
  blender -b --factory-startup -P tools_src/build_combat_animations.py
Output: art/animations/combat.glb (animations only), imported by Godot as the "combat" AnimationLibrary.
"""

import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

PROJECT_DIR = Path(__file__).resolve().parent.parent
RIG_SOURCE = PROJECT_DIR / "art" / "characters" / "adventurer_male.gltf"
GUARD_SOURCE = PROJECT_DIR / "art" / "animations" / "ual1.glb"
GUARD_ACTION = "Punch_Jab"
SEATED_ACTION = "Sitting_Idle_Loop"  # base of the seated clips, so they keep the library's seat height and legs
OUTPUT_PATH = PROJECT_DIR / "art" / "animations" / "combat.glb"
FRAMES_PER_SECOND = 60
SPINE = ("spine_01", "spine_02", "spine_03")
SIDES = ("l", "r")
# limb: (root bone, middle bone, end bone, bone whose head is the limb root)
LIMBS = {
    "hand_l": ("upperarm_l", "lowerarm_l", "hand_l"), "hand_r": ("upperarm_r", "lowerarm_r", "hand_r"),
    "foot_l": ("thigh_l", "calf_l", "foot_l"), "foot_r": ("thigh_r", "calf_r", "foot_r"),
}
POLE_OF_LIMB = {"hand_l": "elbow_l", "hand_r": "elbow_r", "foot_l": "knee_l", "foot_r": "knee_r"}
TURN_OF_END = {"hand_l": "fist_l", "hand_r": "fist_r", "foot_l": "sole_l", "foot_r": "sole_r"}
# A toe on the ground gives back this share of the foot's pitch, so it stays flat when the heel lifts.
MOVED_BONES = ("root", "pelvis")
TOE_FLATTEN = 0.8
# Above this height over its guard position a foot is in the air and its toe follows it rigidly.
TOE_GROUND_HEIGHT = 0.12


def turn(yaw: float, pitch: float, roll: float) -> Matrix:
    """World rotation from degrees: yaw to the character's left, pitch leaning forward, roll leaning left
    (the character faces -Y)."""
    return Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(pitch), 3, "X") @ Matrix.Rotation(math.radians(roll), 3, "Y")


def frame_of(direction: Vector, towards: Vector) -> Matrix:
    """Orthonormal frame with Y along direction and X as close to `towards` as it can be."""
    axis = direction.normalized()
    side = towards - axis * towards.dot(axis)
    side = side.normalized() if side.length > 1e-6 else axis.orthogonal().normalized()

    return Matrix((side, axis, side.cross(axis))).transposed()


def bend_point(root: Vector, end: Vector, first: float, second: float, pole: Vector) -> tuple:
    """Middle joint of a two-bone limb and its end as far as the limb reaches towards `end`."""
    reach = end - root
    distance = min(max(reach.length, abs(first - second) + 1e-4), first + second - 1e-4)
    axis = reach.normalized()
    along = (first * first - second * second + distance * distance) / (2.0 * distance)
    out = pole - axis * pole.dot(axis)
    out = out.normalized() if out.length > 1e-6 else axis.orthogonal().normalized()

    return root + axis * along + out * math.sqrt(max(first * first - along * along, 0.0)), root + axis * distance


def spline(keys: list, time: float):
    """Catmull-Rom through (time, value) keys with time-aware tangents; value is a float or a Vector."""
    if time <= keys[0][0]:
        return keys[0][1]

    if time >= keys[-1][0]:
        return keys[-1][1]

    index = next(i for i in range(len(keys) - 1) if keys[i][0] <= time < keys[i + 1][0])
    (t1, p1), (t2, p2) = keys[index], keys[index + 1]
    t0, p0 = keys[index - 1] if index > 0 else (t1 - (t2 - t1), p1)
    t3, p3 = keys[index + 2] if index + 2 < len(keys) else (t2 + (t2 - t1), p2)
    span = t2 - t1
    m1 = (p2 - p0) * (span / (t2 - t0))
    m2 = (p3 - p1) * (span / (t3 - t1))
    s = (time - t1) / span
    s2, s3 = s * s, s * s * s

    return p1 * (2 * s3 - 3 * s2 + 1) + m1 * (s3 - 2 * s2 + s) + p2 * (-2 * s3 + 3 * s2) + m2 * (s3 - s2)


class Rig:
    """The armature in its guard pose: where every joint is, how every bone is turned, how long the limbs are."""

    def __init__(self, armature) -> None:
        self.armature = armature
        self.bones = [bone.name for bone in armature.data.bones]  # parents come before children
        self.parent = {bone.name: bone.parent.name if bone.parent else None for bone in armature.data.bones}
        self.rest_local = {bone.name: (bone.parent.matrix_local.inverted() @ bone.matrix_local if bone.parent else bone.matrix_local.copy()) for bone in armature.data.bones}
        self.guard_basis = {bone.name: bone.matrix_basis.copy() for bone in armature.pose.bones}
        self.guard = {bone.name: bone.matrix.copy() for bone in armature.pose.bones}
        self.guard_turn = {name: matrix.to_3x3().normalized() for name, matrix in self.guard.items()}
        self.joint = {name: matrix.translation.copy() for name, matrix in self.guard.items()}
        self.lengths = {limb: ((self.joint[middle] - self.joint[root]).length, (self.joint[end] - self.joint[middle]).length) for limb, (root, middle, end) in LIMBS.items()}
        self.guard_pole = {limb: self.joint[middle] - (self.joint[root] + self.joint[end]) / 2.0 for limb, (root, middle, end) in LIMBS.items()}
        self.guard_heading = {side: self.heading(self.joint[f"ball_{side}"] - self.joint[f"foot_{side}"]) for side in SIDES}
        self.toe_turns = {}

    @staticmethod
    def heading(toe: Vector) -> float:
        """Degrees the toes point to the character's left of straight ahead."""
        return math.degrees(math.atan2(toe.x, -toe.y))

    def guard_channels(self) -> dict:
        channels = {"pelvis": self.joint["pelvis"].copy(), "hips": Vector((0.0, 0.0, 0.0)), "chest": Vector((0.0, 0.0, 0.0)), "head": Vector((0.0, 0.0, 0.0))}

        for limb, (_, _, end) in LIMBS.items():
            channels[limb] = self.joint[end].copy()
            channels[POLE_OF_LIMB[limb]] = self.guard_pole[limb].normalized()
            channels[TURN_OF_END[limb]] = Vector((self.guard_heading[limb[-1]] if limb.startswith("foot") else 0.0, 0.0, 0.0))

        return channels

    def solve(self, pose: dict) -> dict:
        """Armature-space matrix of every bone for one set of channel values."""
        hips = turn(*pose["hips"])
        chest = pose["chest"]
        spine_turns = {name: hips @ turn(*(chest * ((index + 1) / len(SPINE)))) for index, name in enumerate(SPINE)}
        head_turn = turn(*pose["head"])
        turns = {"pelvis": hips, **spine_turns, "Head": head_turn, "neck_01": spine_turns[SPINE[-1]].to_quaternion().slerp(head_turn.to_quaternion(), 0.5).to_matrix()}
        turns.update({f"clavicle_{side}": spine_turns[SPINE[-1]] for side in SIDES})
        world = {}

        for name in self.bones:
            parent = self.parent[name]
            carried = world[parent] @ self.rest_local[name] if parent else self.rest_local[name].copy()

            if name == "pelvis":
                world[name] = Matrix.Translation(pose["pelvis"]) @ (hips @ self.guard_turn[name]).to_4x4()
            elif name in turns:
                world[name] = Matrix.Translation(carried.translation) @ (turns[name] @ self.guard_turn[name]).to_4x4()
            else:
                world[name] = carried @ self.guard_basis[name]

            limb = next((key for key, chain in LIMBS.items() if chain[2] == name), None)

            if limb:
                self.solve_limb(limb, pose, world)

        return world

    def solve_limb(self, limb: str, pose: dict, world: dict) -> None:
        """Re-aims the three bones of a limb once its end bone has been reached in the walk down the skeleton."""
        root, middle, end = LIMBS[limb]
        first, second = self.lengths[limb]
        root_point = world[root].translation.copy()
        middle_point, end_point = bend_point(root_point, pose[limb], first, second, pose[POLE_OF_LIMB[limb]])
        guard_frames = (frame_of(self.joint[middle] - self.joint[root], self.guard_pole[limb]), frame_of(self.joint[end] - self.joint[middle], self.guard_pole[limb]))
        pole = middle_point - (root_point + end_point) / 2.0
        pose_frames = (frame_of(middle_point - root_point, pole), frame_of(end_point - middle_point, pole))
        upper_turn = pose_frames[0] @ guard_frames[0].transposed()
        lower_turn = pose_frames[1] @ guard_frames[1].transposed()
        yaw, pitch, roll = pose[TURN_OF_END[limb]]
        side = limb[-1]
        from_guard = Matrix.Rotation(math.radians(-self.guard_heading[side]), 3, "Z")
        # a hand rides on its forearm, twists about it (yaw) and bends at the wrist about the elbow's hinge (pitch);
        # a foot is aimed in the world, whatever the shin does
        forearm = (self.joint[end] - self.joint[middle]).normalized()
        hinge = forearm.cross(self.guard_pole[limb]).normalized()
        hand_turn = lower_turn @ Matrix.Rotation(math.radians(yaw), 3, forearm) @ Matrix.Rotation(math.radians(pitch), 3, hinge)
        end_turn = hand_turn if limb.startswith("hand") else turn(yaw, pitch, roll) @ from_guard

        world[root] = Matrix.Translation(root_point) @ (upper_turn @ self.guard_turn[root]).to_4x4()
        world[middle] = Matrix.Translation(middle_point) @ (lower_turn @ self.guard_turn[middle]).to_4x4()
        world[end] = Matrix.Translation(end_point) @ (end_turn @ self.guard_turn[end]).to_4x4()

        if limb.startswith("foot"):
            grounded = min(max(1.0 - (end_point.z - self.joint[end].z) / TOE_GROUND_HEIGHT, 0.0), 1.0)
            self.toe_turns[f"ball_{side}"] = turn(yaw, pitch * (1.0 - TOE_FLATTEN * grounded), roll) @ from_guard

    def finish_toes(self, world: dict) -> None:
        for toe, toe_turn in self.toe_turns.items():
            foot = self.parent[toe]
            carried = world[foot] @ self.rest_local[toe]
            world[toe] = Matrix.Translation(carried.translation) @ (toe_turn @ self.guard_turn[toe]).to_4x4()
            leaf = next((name for name in self.bones if self.parent[name] == toe), None)

            if leaf:
                world[leaf] = world[toe] @ self.rest_local[leaf] @ self.guard_basis[leaf]

    def apply(self, world: dict, frame: int) -> None:
        for name in self.bones:
            parent = self.parent[name]
            carried = world[parent] @ self.rest_local[name] if parent else self.rest_local[name]
            bone = self.armature.pose.bones[name]

            bone.matrix_basis = carried.inverted() @ world[name]
            bone.keyframe_insert("rotation_quaternion", frame=frame)

            if name == "pelvis":
                bone.keyframe_insert("location", frame=frame)


def V(x: float, y: float, z: float) -> Vector:
    return Vector((x, y, z))


def clip_keys(rig: Rig, seconds: float, poses: list, base: dict | None = None) -> dict:
    """Per channel, the (time, value) keys of a clip. A pose names only the channels it sets, as offsets from
    the guard (positions in metres: x to the character's left, y backwards, z up; turns in degrees). Two kinds
    of channel are absolute instead: limb poles (the direction the elbow or knee points) and soles (toe heading
    to the left of straight ahead, toes-down pitch, roll with the instep to the left). Every channel starts and
    ends in the guard. A looping clip (riding) gives a base pose instead: it starts and ends there, and its key
    poses are offsets from the base."""
    guard = rig.guard_channels()
    poles = set(POLE_OF_LIMB.values())
    soles = {"sole_l", "sole_r"}
    absolutes = poles | soles
    base = base or {}
    rest = {channel: (base[channel].normalized() if channel in poles else base[channel]) if channel in absolutes and channel in base else value + base.get(channel, Vector((0.0, 0.0, 0.0))) for channel, value in guard.items()}
    keys = {channel: [(0.0, value)] for channel, value in rest.items()}

    for time, pose in poses:
        for channel, value in pose.items():
            absolute = value.normalized() if channel in poles else value
            keys[channel].append((time, absolute if channel in absolutes else rest[channel] + value))

    for channel, value in rest.items():
        keys[channel].append((seconds, value))

    return keys


def bake_clip(rig: Rig, name: str, seconds: float, poses: list, base: dict | None = None) -> None:
    armature = rig.armature
    action = bpy.data.actions.new(name)
    keys = clip_keys(rig, seconds, poses, base)

    armature.animation_data_create()
    armature.animation_data.action = action

    for frame in range(round(seconds * FRAMES_PER_SECOND) + 1):
        time = frame / FRAMES_PER_SECOND
        pose = {channel: spline(channel_keys, time) for channel, channel_keys in keys.items()}
        world = rig.solve(pose)

        rig.finish_toes(world)
        rig.apply(world, frame)

    track = armature.animation_data.nla_tracks.new()
    track.name = name
    track.strips.new(name, 0, action)
    armature.animation_data.action = None
    print(f"CLIP {name} {seconds:.2f}s")


# Key poses. Stance of the guard: left foot and left hand lead, right side behind; the target is in front (-Y).
# Guard soles: left foot heads -6 degrees, right foot -44 (turned out).
CLIPS = {
    # breathing and a small bounce, to stand in guard between blows
    "Fight_Idle_Loop": (1.4, [
        (0.35, {"pelvis": V(0.0, 0.0, -0.012), "hand_l": V(0.0, 0.005, -0.012), "hand_r": V(0.0, 0.0, -0.01), "chest": V(0.0, 1.5, 0.0)}),
        (0.70, {"pelvis": V(0.004, 0.0, 0.0), "hand_l": V(0.004, 0.0, 0.004), "hand_r": V(0.0, 0.0, 0.003)}),
        (1.05, {"pelvis": V(0.0, 0.0, -0.012), "hand_l": V(0.0, -0.005, -0.01), "hand_r": V(0.0, 0.0, -0.012), "chest": V(0.0, 1.5, 0.0)}),
    ]),
    # rear-leg push kick: weight over the lead leg, knee up, heel driven out by the hips, back the same way
    "Kick_Front": (0.90, [
        (0.10, {"pelvis": V(0.07, -0.04, -0.02), "hips": V(6.0, 0.0, 0.0), "foot_r": V(0.0, -0.02, 0.05), "sole_r": V(-40.0, 28.0, 0.0), "hand_r": V(0.03, 0.02, 0.03)}),
        (0.24, {"pelvis": V(0.11, -0.06, 0.02), "hips": V(14.0, -8.0, 0.0), "chest": V(0.0, 10.0, 0.0), "foot_r": V(0.14, -0.50, 0.58), "sole_r": V(-10.0, 30.0, 0.0), "knee_r": V(-0.05, -1.0, 0.75), "sole_l": V(12.0, 0.0, 0.0), "hand_r": V(0.05, 0.03, 0.05), "hand_l": V(0.02, 0.06, -0.02)}),
        (0.34, {"pelvis": V(0.11, -0.17, 0.03), "hips": V(18.0, -26.0, 0.0), "chest": V(0.0, 12.0, 0.0), "head": V(0.0, 4.0, 0.0), "foot_r": V(0.16, -1.36, 0.88), "sole_r": V(0.0, -35.0, 0.0), "knee_r": V(0.0, -0.4, 1.0), "sole_l": V(18.0, 0.0, 0.0), "hand_r": V(-0.10, 0.20, -0.22), "hand_l": V(0.02, 0.07, -0.03)}),
        (0.40, {"pelvis": V(0.11, -0.18, 0.03), "hips": V(18.0, -27.0, 0.0), "foot_r": V(0.16, -1.38, 0.89), "sole_r": V(0.0, -38.0, 0.0), "hand_r": V(-0.11, 0.22, -0.24)}),
        (0.54, {"pelvis": V(0.10, -0.07, 0.02), "hips": V(12.0, -8.0, 0.0), "chest": V(0.0, 8.0, 0.0), "foot_r": V(0.13, -0.55, 0.55), "sole_r": V(-10.0, 25.0, 0.0), "knee_r": V(-0.05, -1.0, 0.7), "sole_l": V(12.0, 0.0, 0.0), "hand_r": V(0.0, 0.08, -0.05)}),
        (0.72, {"pelvis": V(0.02, 0.0, -0.03), "hips": V(2.0, 0.0, 0.0), "foot_r": V(0.0, 0.0, 0.01), "sole_r": V(-40.0, 8.0, 0.0), "hand_r": V(0.0, 0.0, -0.02), "hand_l": V(0.0, 0.0, -0.02)}),
    ]),
    # rear-leg roundhouse: support foot turns out, hips roll over, the shin whips across at rib height
    "Kick_Roundhouse": (1.00, [
        (0.10, {"pelvis": V(0.08, -0.03, -0.02), "hips": V(18.0, 0.0, 0.0), "sole_l": V(30.0, 0.0, 0.0), "foot_r": V(-0.02, -0.02, 0.05), "sole_r": V(-40.0, 30.0, 0.0), "hand_r": V(-0.04, -0.03, 0.03)}),
        (0.24, {"pelvis": V(0.13, -0.05, 0.03), "hips": V(58.0, -4.0, 14.0), "chest": V(-12.0, 0.0, 6.0), "head": V(0.0, 0.0, 6.0), "sole_l": V(75.0, 0.0, 0.0), "knee_l": V(0.97, -0.26, 0.1), "foot_r": V(-0.36, -0.22, 0.92), "sole_r": V(-60.0, 40.0, 40.0), "knee_r": V(-0.8, -0.9, 0.5), "hand_r": V(-0.05, -0.02, 0.0), "hand_l": V(-0.04, 0.05, 0.02)}),
        (0.33, {"pelvis": V(0.15, -0.10, 0.04), "hips": V(104.0, -6.0, 26.0), "chest": V(-26.0, 0.0, 8.0), "head": V(0.0, 0.0, 10.0), "sole_l": V(115.0, 0.0, 0.0), "knee_l": V(0.9, 0.42, 0.1), "foot_r": V(0.24, -1.28, 1.02), "sole_r": V(12.0, 12.0, 80.0), "knee_r": V(-0.3, -0.8, 0.6), "hand_r": V(-0.26, 0.26, -0.30), "elbow_r": V(-0.6, 0.6, -0.5), "hand_l": V(-0.10, 0.08, 0.03)}),
        (0.39, {"pelvis": V(0.15, -0.10, 0.04), "hips": V(112.0, -6.0, 26.0), "chest": V(-28.0, 0.0, 8.0), "sole_l": V(118.0, 0.0, 0.0), "foot_r": V(0.42, -1.18, 1.00), "sole_r": V(22.0, 12.0, 82.0), "hand_r": V(-0.30, 0.30, -0.34)}),
        (0.54, {"pelvis": V(0.12, -0.05, 0.03), "hips": V(64.0, -4.0, 14.0), "chest": V(-12.0, 0.0, 6.0), "head": V(0.0, 0.0, 6.0), "sole_l": V(80.0, 0.0, 0.0), "knee_l": V(0.98, -0.17, 0.1), "foot_r": V(-0.30, -0.28, 0.86), "sole_r": V(-55.0, 40.0, 40.0), "knee_r": V(-0.8, -0.9, 0.5), "hand_r": V(-0.10, 0.10, -0.10)}),
        (0.78, {"pelvis": V(0.02, 0.0, -0.035), "hips": V(4.0, 0.0, 0.0), "sole_l": V(-2.0, 0.0, 0.0), "foot_r": V(0.0, 0.0, 0.01), "sole_r": V(-42.0, 6.0, 0.0), "hand_r": V(0.0, 0.0, -0.02), "hand_l": V(0.0, 0.0, -0.02)}),
    ]),
    # lead-leg side kick: the body turns side-on, knee to the chest, heel thrust straight out, trunk leaning away
    "Kick_Side": (1.05, [
        (0.13, {"pelvis": V(-0.10, 0.10, -0.03), "hips": V(-35.0, 0.0, 0.0), "sole_r": V(-84.0, 0.0, 0.0), "knee_r": V(-0.99, -0.1, 0.1), "foot_l": V(-0.03, 0.03, 0.05), "sole_l": V(-36.0, 25.0, 0.0), "hand_l": V(-0.03, 0.04, -0.02)}),
        (0.28, {"pelvis": V(-0.17, 0.20, 0.02), "hips": V(-78.0, 0.0, -10.0), "chest": V(10.0, 0.0, -4.0), "head": V(0.0, 0.0, -6.0), "sole_r": V(-154.0, 0.0, 0.0), "knee_r": V(-0.44, 0.9, 0.1), "foot_l": V(-0.22, 0.02, 0.62), "sole_l": V(-88.0, 10.0, -25.0), "knee_l": V(0.3, -1.0, 0.9), "hand_l": V(-0.10, 0.06, -0.12), "hand_r": V(0.06, 0.02, 0.0)}),
        (0.38, {"pelvis": V(-0.19, 0.16, 0.03), "hips": V(-88.0, 0.0, -30.0), "chest": V(8.0, 0.0, -10.0), "head": V(0.0, 0.0, -14.0), "sole_r": V(-188.0, 0.0, 0.0), "knee_r": V(0.14, 0.99, 0.1), "foot_l": V(-0.22, -1.06, 0.92), "sole_l": V(-98.0, 0.0, -72.0), "knee_l": V(0.2, -0.6, 1.0), "hand_l": V(-0.12, -0.10, -0.26), "elbow_l": V(0.3, -0.2, -1.0), "hand_r": V(0.08, 0.04, -0.02)}),
        (0.45, {"pelvis": V(-0.19, 0.15, 0.03), "hips": V(-88.0, 0.0, -31.0), "sole_r": V(-190.0, 0.0, 0.0), "foot_l": V(-0.22, -1.08, 0.93), "sole_l": V(-98.0, 0.0, -75.0), "hand_l": V(-0.12, -0.11, -0.27)}),
        (0.60, {"pelvis": V(-0.16, 0.19, 0.02), "hips": V(-76.0, 0.0, -10.0), "chest": V(10.0, 0.0, -4.0), "head": V(0.0, 0.0, -6.0), "sole_r": V(-154.0, 0.0, 0.0), "knee_r": V(-0.44, 0.9, 0.1), "foot_l": V(-0.20, 0.0, 0.58), "sole_l": V(-88.0, 10.0, -25.0), "knee_l": V(0.3, -1.0, 0.9), "hand_l": V(-0.08, 0.04, -0.10)}),
        (0.84, {"pelvis": V(-0.01, 0.01, -0.035), "hips": V(-4.0, 0.0, 0.0), "sole_r": V(-48.0, 0.0, 0.0), "foot_l": V(0.0, 0.0, 0.01), "sole_l": V(-6.0, 6.0, 0.0), "hand_l": V(0.0, 0.0, -0.02), "hand_r": V(0.0, 0.0, -0.02)}),
    ]),
    # rear uppercut: dip and coil to the rear side, then legs and hips throw the fist up the centre line
    "Punch_Uppercut": (0.70, [
        (0.11, {"pelvis": V(-0.03, 0.02, -0.13), "hips": V(-18.0, 6.0, -5.0), "chest": V(-12.0, 12.0, -10.0), "hand_r": V(0.02, -0.02, -0.30), "elbow_r": V(-0.3, 0.9, -0.4), "hand_l": V(-0.02, 0.05, 0.0)}),
        (0.21, {"pelvis": V(0.03, -0.05, 0.03), "hips": V(30.0, -4.0, 2.0), "chest": V(16.0, -8.0, 4.0), "head": V(0.0, -3.0, 0.0), "hand_r": V(0.25, -0.33, 0.11), "elbow_r": V(-0.3, 0.2, -1.0), "fist_r": V(60.0, 0.0, 0.0), "foot_r": V(0.02, -0.04, 0.05), "sole_r": V(-22.0, 34.0, 0.0), "hand_l": V(-0.05, 0.10, -0.02)}),
        (0.27, {"pelvis": V(0.03, -0.05, 0.04), "hips": V(34.0, -5.0, 2.0), "chest": V(18.0, -10.0, 4.0), "hand_r": V(0.26, -0.31, 0.19), "fist_r": V(60.0, 0.0, 0.0), "foot_r": V(0.02, -0.04, 0.06), "sole_r": V(-20.0, 38.0, 0.0)}),
        (0.44, {"pelvis": V(0.01, -0.01, -0.01), "hips": V(8.0, 0.0, 0.0), "chest": V(4.0, 0.0, 0.0), "hand_r": V(0.08, -0.08, 0.06), "fist_r": V(15.0, 0.0, 0.0), "foot_r": V(0.0, -0.01, 0.01), "sole_r": V(-40.0, 8.0, 0.0)}),
    ]),
    # lead hook: short coil, then the whole lead side turns in with the elbow up and the forearm level
    "Punch_Hook": (0.62, [
        (0.09, {"pelvis": V(0.03, 0.0, -0.03), "hips": V(12.0, 0.0, 0.0), "chest": V(10.0, 2.0, 0.0), "hand_l": V(0.10, 0.12, -0.03), "elbow_l": V(1.0, 0.4, -0.2), "hand_r": V(0.02, 0.03, 0.02)}),
        (0.18, {"pelvis": V(-0.02, -0.03, -0.01), "hips": V(-34.0, 0.0, 0.0), "chest": V(-30.0, 4.0, 0.0), "foot_l": V(0.0, 0.0, 0.03), "sole_l": V(-44.0, 18.0, 0.0), "hand_l": V(-0.13, -0.19, 0.0), "elbow_l": V(1.0, 0.1, 0.45), "fist_l": V(-50.0, 0.0, 0.0), "hand_r": V(0.04, 0.05, 0.04)}),
        (0.24, {"pelvis": V(-0.02, -0.03, -0.01), "hips": V(-42.0, 0.0, 0.0), "chest": V(-38.0, 4.0, 0.0), "sole_l": V(-50.0, 20.0, 0.0), "foot_l": V(0.0, 0.0, 0.03), "hand_l": V(-0.27, -0.13, 0.0), "elbow_l": V(1.0, 0.0, 0.45), "fist_l": V(-50.0, 0.0, 0.0)}),
        (0.42, {"pelvis": V(0.0, 0.0, -0.015), "hips": V(-8.0, 0.0, 0.0), "chest": V(-8.0, 0.0, 0.0), "sole_l": V(-12.0, 4.0, 0.0), "foot_l": V(0.0, 0.0, 0.005), "hand_l": V(-0.08, -0.02, 0.0), "fist_l": V(-10.0, 0.0, 0.0)}),
    ]),
}


# Riding the Mula (features/mobs/mula_mount.gd): seated on its back, legs straddling the barrel with the knees
# forward and out, hands ahead on the broken chains of the neck. Offsets from the guard; poles and soles absolute.
RIDE_BASE = {
    "pelvis": V(-0.018, 0.0, 0.0), "chest": V(0.0, 8.0, 0.0),
    "foot_l": V(0.186, -0.2, 0.13), "knee_l": V(0.5, -1.0, 0.0), "sole_l": V(0.0, 10.0, 0.0),
    "foot_r": V(-0.241, -0.62, 0.13), "knee_r": V(-0.5, -1.0, 0.0), "sole_r": V(0.0, 10.0, 0.0),
    "hand_l": V(0.037, -0.25, -0.40), "elbow_l": V(0.6, 0.5, -0.6),
    "hand_r": V(0.081, -0.417, -0.305), "elbow_r": V(-0.6, 0.5, -0.6),
}
# The Saci (tools_src/build_saci.py) has no right leg: he stands on the left foot under his middle, the stump
# of the right thigh a little forward, arms loose and out for balance.
SACI_BASE = {
    "pelvis": V(0.09, -0.04, 0.07), "hips": V(0.0, 0.0, 0.0), "chest": V(0.0, -10.0, 0.0), "head": V(0.0, -32.0, 0.0),
    "foot_l": V(-0.12, 0.08, 0.0), "knee_l": V(0.2, -1.0, 0.0), "sole_l": V(0.0, 0.0, 0.0),
    "foot_r": V(0.04, -0.22, 0.12), "knee_r": V(-0.3, -1.0, 0.2), "sole_r": V(0.0, 30.0, 0.0),
    "hand_l": V(0.20, 0.25, -0.58), "elbow_l": V(0.5, 0.8, -0.2),
    "hand_r": V(-0.12, 0.08, -0.48), "elbow_r": V(-0.5, 0.8, -0.2),
}
# Looping clips from a base pose: name -> (seconds, base, key poses as offsets from the base).
LOOP_CLIPS = {
    # the Saci standing on his one leg: a small bob and the arms swinging for balance
    "Saci_Idle_Loop": (1.8, SACI_BASE, [
        (0.45, {"pelvis": V(0.012, 0.0, -0.015), "hand_l": V(0.03, 0.0, 0.04), "hand_r": V(-0.02, 0.0, 0.02), "chest": V(-3.0, 0.0, 2.0)}),
        (0.9, {"pelvis": V(0.0, 0.0, 0.0)}),
        (1.35, {"pelvis": V(-0.01, 0.0, -0.015), "hand_l": V(0.01, 0.0, 0.02), "hand_r": V(-0.04, 0.0, 0.04), "chest": V(3.0, 0.0, -2.0)}),
    ]),
    # one hop on the left foot: crouch, spring (the whole body leaves the ground, toes pointed), land soft
    "Saci_Hop_Loop": (0.5, SACI_BASE, [
        (0.09, {"pelvis": V(0.0, -0.02, -0.09), "chest": V(0.0, 8.0, 0.0), "hand_l": V(0.04, 0.08, -0.04), "hand_r": V(-0.04, 0.08, -0.04)}),
        (0.25, {"pelvis": V(0.0, -0.02, 0.16), "foot_l": V(0.0, 0.03, 0.17), "sole_l": V(0.0, -35.0, 0.0), "chest": V(0.0, -2.0, 0.0), "hand_l": V(0.10, -0.06, 0.18), "hand_r": V(-0.10, -0.06, 0.18), "foot_r": V(0.0, 0.0, 0.10)}),
        (0.40, {"pelvis": V(0.0, -0.01, -0.07), "chest": V(0.0, 6.0, 0.0), "hand_l": V(0.03, 0.04, -0.02), "hand_r": V(-0.03, 0.04, -0.02)}),
    ]),
    # sitting still on the Mula: slow breathing
    "Ride_Idle_Loop": (2.4, RIDE_BASE, [
        (1.2, {"pelvis": V(0.0, 0.0, -0.008), "chest": V(0.0, 2.0, 0.0), "hand_l": V(0.0, 0.0, -0.01), "hand_r": V(0.0, 0.0, -0.01)}),
    ]),
    # galloping (and flying): the seat rises and falls once per stride, the trunk leans in, the hands ride along
    "Ride_Gallop_Loop": (0.6, RIDE_BASE, [
        (0.15, {"pelvis": V(0.0, -0.02, 0.05), "chest": V(0.0, 12.0, 0.0), "hand_l": V(0.0, -0.05, 0.03), "hand_r": V(0.0, -0.05, 0.03)}),
        (0.45, {"pelvis": V(0.0, 0.01, -0.03), "chest": V(0.0, 6.0, 0.0), "hand_l": V(0.0, 0.02, -0.03), "hand_r": V(0.0, 0.02, -0.03)}),
    ]),
}

# The couple on the plaza bench (tools_src/build_hub_scene.py, add_couple): she sits on his left, hip to hip, and
# they talk in turns of TALK_TURN seconds (WalkingNpc.talk_turn_seconds opens the mouth of whoever has the turn):
# he talks first, she listens, then she talks and he listens. Offsets from the library's Sitting_Idle.
# He: the left forearm lies across her shoulders, the elbow behind her near shoulder blade, the hand bent over her far
# shoulder; the
# right hand rests on his thigh and gestures while he talks; head turned to her.
TALK_TURN = 4.0
EMBRACE_BASE = {
    "chest": V(6.0, 0.0, 5.0), "head": V(18.0, 0.0, 6.0),
    "hand_l": V(0.371, 0.136, 0.472), "elbow_l": V(0.0, 1.0, 0.0), "fist_l": V(0.0, -18.0, 0.0),
    "hand_r": V(0.02, -0.06, 0.02),
}
# She: trunk a little forward and toward him (his arm passes behind her shoulders), head turned to him, her right
# hand on his knee, the left one in her lap, gesturing while she talks.
LEAN_BASE = {
    "chest": V(-6.0, 8.0, -4.0), "head": V(-20.0, 2.0, -10.0),
    "hand_r": V(-0.12, -0.13, -0.02), "elbow_r": V(-0.5, 0.7, -0.4),
    "hand_l": V(-0.1, -0.02, 0.0),
}
NOD = {"head": V(0.0, 6.0, 0.0)}
STILL_HEAD = {"head": V(0.0, 0.0, 0.0)}
SEATED_CLIPS = {
    "Couple_Embrace_Loop": (2.0 * TALK_TURN, EMBRACE_BASE, [
        (1.0, {"head": V(2.0, -4.0, 0.0), "hand_r": V(0.04, -0.10, 0.12), "fist_r": V(-30.0, 0.0, 0.0)}),
        (2.0, {"head": V(-2.0, 3.0, 0.0), "hand_r": V(0.06, -0.12, 0.08), "fist_r": V(-20.0, 0.0, 0.0), "chest": V(0.0, 1.5, 0.0)}),
        (3.0, {"head": V(3.0, -2.0, 0.0), "hand_r": V(0.03, -0.08, 0.12), "fist_r": V(-35.0, 0.0, 0.0)}),
        (TALK_TURN, {**STILL_HEAD, "hand_r": V(0.0, 0.0, 0.0), "fist_r": V(0.0, 0.0, 0.0), "chest": V(0.0, 0.0, 0.0)}),
        (5.2, NOD), (5.6, STILL_HEAD),
        (6.0, {"chest": V(0.0, 1.5, 0.0)}),
        (6.8, NOD), (7.2, STILL_HEAD),
    ]),
    "Couple_Lean_Loop": (2.0 * TALK_TURN, LEAN_BASE, [
        (1.2, NOD), (1.6, STILL_HEAD),
        (2.0, {"chest": V(0.0, 1.5, 0.0)}),
        (2.8, NOD), (3.2, STILL_HEAD),
        (TALK_TURN, {"hand_l": V(0.0, 0.0, 0.0), "fist_l": V(0.0, 0.0, 0.0), "chest": V(0.0, 0.0, 0.0)}),
        (5.0, {"head": V(-3.0, -3.0, 2.0), "hand_l": V(-0.03, -0.10, 0.10), "fist_l": V(30.0, 0.0, 0.0)}),
        (6.0, {"head": V(2.0, 2.0, -2.0), "hand_l": V(-0.05, -0.12, 0.07), "fist_l": V(20.0, 0.0, 0.0), "chest": V(0.0, 1.5, 0.0)}),
        (7.0, {"head": V(-2.0, -2.0, 0.0), "hand_l": V(-0.02, -0.08, 0.11), "fist_l": V(35.0, 0.0, 0.0)}),
    ]),
}


def local_matrix(bone, matrix_of) -> Matrix:
    return matrix_of(bone.parent).inverted() @ matrix_of(bone) if bone.parent else matrix_of(bone)


def copy_library_pose(armature, library) -> None:
    """Poses the character with the library's own local transforms, which is what the engine plays.

    The library skeleton rests in another stance (same bone axes, neck and chest set differently),
    and Blender would apply the action relative to each rest: the guard would come out bent by that
    difference and every clip would jump when chained with a library one. Only the moved bones
    (root, pelvis) take the position, the others keep the character's own proportions.
    """
    for bone in armature.pose.bones:
        rest_local = local_matrix(bone.bone, lambda rest_bone: rest_bone.matrix_local)
        library_local = local_matrix(library.pose.bones[bone.name], lambda pose_bone: pose_bone.matrix)
        from_rest = rest_local.inverted() @ library_local

        bone.rotation_mode = "QUATERNION"
        bone.rotation_quaternion = from_rest.to_quaternion()
        bone.location = from_rest.translation if bone.name in MOVED_BONES else Vector((0.0, 0.0, 0.0))

    bpy.context.view_layer.update()


def load_rigs(base_actions: tuple) -> dict:
    """One Rig per base pose of the library (its first frame), all on the same character armature."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(RIG_SOURCE))

    armature = next(scene_object for scene_object in bpy.data.objects if scene_object.type == "ARMATURE")
    rig_objects = set(bpy.data.objects)

    bpy.ops.import_scene.gltf(filepath=str(GUARD_SOURCE))

    library = next(scene_object for scene_object in set(bpy.data.objects) - rig_objects if scene_object.type == "ARMATURE")
    rigs = {}

    library.animation_data_create()

    for action_name in base_actions:
        action = bpy.data.actions[action_name]
        library.animation_data.action = action

        if action.slots:
            library.animation_data.action_slot = action.slots[0]

        bpy.context.scene.frame_set(int(action.frame_range[0]))
        bpy.context.view_layer.update()
        copy_library_pose(armature, library)
        rigs[action_name] = Rig(armature)

    for scene_object in set(bpy.data.objects) - rig_objects:
        bpy.data.objects.remove(scene_object, do_unlink=True)

    for action in list(bpy.data.actions):
        bpy.data.actions.remove(action)

    return rigs


def export_clips(armature) -> None:
    for scene_object in list(bpy.data.objects):
        if scene_object.type == "MESH":
            bpy.data.objects.remove(scene_object, do_unlink=True)

    bpy.ops.object.select_all(action="DESELECT")
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.gltf(filepath=str(OUTPUT_PATH), export_format="GLB", use_selection=True, export_animations=True, export_animation_mode="NLA_TRACKS", export_force_sampling=True, export_optimize_animation_size=False, export_yup=True)


if __name__ == "__main__":
    base_rigs = load_rigs((GUARD_ACTION, SEATED_ACTION))
    combat_rig = base_rigs[GUARD_ACTION]

    bpy.context.scene.render.fps = FRAMES_PER_SECOND

    for clip_name, (clip_seconds, clip_poses) in CLIPS.items():
        bake_clip(combat_rig, clip_name, clip_seconds, clip_poses)

    for clip_name, (clip_seconds, clip_base, clip_poses) in LOOP_CLIPS.items():
        bake_clip(combat_rig, clip_name, clip_seconds, clip_poses, clip_base)

    for clip_name, (clip_seconds, clip_base, clip_poses) in SEATED_CLIPS.items():
        bake_clip(base_rigs[SEATED_ACTION], clip_name, clip_seconds, clip_poses, clip_base)

    export_clips(combat_rig.armature)
    print(f"BUILT {OUTPUT_PATH}")
