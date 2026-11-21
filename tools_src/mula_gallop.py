"""Run action of the Mula sem cabeça: a real horse gallop, keyed procedurally on the CC0 horse skeleton.

Drawn after Muybridge's photographs of a galloping horse (The Horse in Motion, 1878; public domain): a transverse
gallop on the right lead, four beats -- left hind, right hind, left fore, right fore -- then one suspension with
every leg gathered under the belly. Each leg plants forward and sweeps back while on the ground, then folds
(knee of the fore leg back, hock of the hind leg forward) and swings forward in the air. The trunk bobs so the
planted hooves stay on the ground and flies during the suspension; the back rounds when the legs gather and
stretches when they reach out; the neck stump dips as the fore legs land and the tail streams and waves.

The cycle is short (CYCLE_FRAMES at FPS): the mount runs at 15-25 m/s.
"""

import math

import bpy
from mathutils import Quaternion, Vector

FPS = 24
CYCLE_FRAMES = 12  # 0,5 s por passada
DUTY = 0.38  # parte do ciclo em que cada pata fica no chão: a suspensão fica em ~1/5 do ciclo, como nas fotos
SUSPENSION_LIFT = 0.45  # quanto o tronco sobe no meio da suspensão (unidades do pacote, ~3,4 por metro)
# Pata: (osso de cima, osso de baixo, fase em que o casco toca o chão, perfil). Ordem dos tempos: posterior
# esquerdo, posterior direito, anterior esquerdo, anterior direito (mão de dentro), suspensão.
LEGS = (
    ("BackUpLeg.L", "BackLowLeg.L", 0.0, "hind"),
    ("BackUpLeg.R", "BackLowLeg.R", 0.1, "hind"),
    ("FrontUpLeg.L", "FrontLowLeg.L", 0.3, "fore"),
    ("FrontUpLeg.R", "FrontLowLeg.R", 0.42, "fore"),
)
# Graus em torno do eixo X do mundo (positivo = casco para trás): onde a pata toca, onde larga o chão, quanto a
# articulação de baixo dobra no ar (joelho da mão para trás, jarrete da pata para a frente), quanto cede no apoio,
# os expoentes que adiantam (< 1) ou atrasam (> 1) a volta da pata no ar e a dobra (a mão dobra logo ao sair do chão e
# chega esticada na frente; a pata traseira dobra no meio do voo).
PROFILES = {
    "fore": {"reach": -30.0, "push": 28.0, "fold": 80.0, "give": 0.0, "swing_ease": 0.75, "fold_ease": 0.9},
    "hind": {"reach": -24.0, "push": 34.0, "fold": -48.0, "give": -10.0, "swing_ease": 0.7, "fold_ease": 1.0},
}
# Tronco, coluna, pescoço e cauda: (osso, amplitude em graus, fase do pico). Coluna arredonda na suspensão
# (pernas recolhidas) e estica quando as patas se abrem.
WAVES = (
    ("Body", 3.5, 0.55),
    ("Hips", -4.0, 0.85),
    ("Torso", -3.0, 0.9),
    ("Shoulders", 5.0, 0.45),
    ("Neck", 7.0, 0.5),
    ("Back", 3.0, 0.1),
    ("Tail1", -8.0, 0.2),
    ("Tail2", 10.0, 0.35),
    ("Tail3", 12.0, 0.5),
    ("Tail4", 14.0, 0.65),
)
TAIL_LIFT = (("Tail1", -25.0), ("Tail2", -20.0), ("Tail3", -12.0))  # cauda levantada e jogada para trás no galope


def smooth(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def leg_angles(phase: float, profile: dict) -> tuple:
    """(upper, lower) degrees of one leg at a phase measured from its own footfall."""
    if phase < DUTY:
        sweep = phase / DUTY
        return profile["reach"] + (profile["push"] - profile["reach"]) * sweep, profile["give"] * math.sin(math.pi * sweep)

    swing = (phase - DUTY) / (1.0 - DUTY)

    return profile["push"] + (profile["reach"] - profile["push"]) * smooth(swing ** profile["swing_ease"]), profile["fold"] * math.sin(math.pi * swing ** profile["fold_ease"]) ** 1.2


def x_turn(armature, bone_name: str, degrees: float) -> Quaternion:
    """Rotation about the world X axis written in the bone's rest frame (every bone of the rig lies in a plane parallel
    to YZ, so parents turning about X keep that axis)."""
    axis = armature.data.bones[bone_name].matrix_local.to_3x3().inverted() @ Vector((1.0, 0.0, 0.0))

    return Quaternion(axis.normalized(), math.radians(degrees))


def stance_legs(cycle: float) -> list:
    return [lower for _upper, lower, footfall, _kind in LEGS if (cycle - footfall) % 1.0 < DUTY]


def pose_at(armature, cycle: float, lift: float) -> None:
    """Set the rotations for a cycle phase (0..1) and the trunk height (lift, along world Z)."""
    pose_bones = armature.pose.bones

    for pose_bone in pose_bones:
        pose_bone.rotation_mode = "QUATERNION"
        pose_bone.rotation_quaternion = Quaternion()
        pose_bone.location = Vector()

    for upper, lower, footfall, kind in LEGS:
        upper_degrees, lower_degrees = leg_angles((cycle - footfall) % 1.0, PROFILES[kind])
        pose_bones[upper].rotation_quaternion = x_turn(armature, upper, upper_degrees)
        pose_bones[lower].rotation_quaternion = x_turn(armature, lower, lower_degrees)

    for bone_name, degrees, peak in WAVES:
        pose_bones[bone_name].rotation_quaternion = x_turn(armature, bone_name, degrees * math.cos(2.0 * math.pi * (cycle - peak)))

    for bone_name, degrees in TAIL_LIFT:
        pose_bones[bone_name].rotation_quaternion = x_turn(armature, bone_name, degrees) @ pose_bones[bone_name].rotation_quaternion

    body = armature.data.bones["Body"]
    pose_bones["Body"].location = body.matrix_local.to_3x3().inverted() @ Vector((0.0, 0.0, lift))
    bpy.context.view_layer.update()

    for upper, lower, footfall, kind in LEGS:
        follow_hoof(armature, upper, lower, sum(leg_angles((cycle - footfall) % 1.0, PROFILES[kind])) + body_pitch(cycle))


def body_pitch(cycle: float) -> float:
    return WAVES[0][1] * math.cos(2.0 * math.pi * (cycle - WAVES[0][2]))


def follow_hoof(armature, upper: str, lower: str, degrees: float) -> None:
    """The hoof is skinned to the foot bone (a child of the root): carry it to the end of the leg, turned with it."""
    foot_name = upper.replace("UpLeg", "Foot")
    foot = armature.data.bones[foot_name]
    shift = armature.pose.bones[lower].tail - foot.head_local

    armature.pose.bones[foot_name].location = foot.matrix_local.to_3x3().inverted() @ shift
    armature.pose.bones[foot_name].rotation_quaternion = x_turn(armature, foot_name, degrees)


def trunk_heights(armature) -> list:
    """Trunk lift per frame: planted hooves rest on the ground (mean over the legs in stance); during the
    suspension the trunk flies on a parabola between the last and the first planted frames."""
    planted = {}

    for frame in range(CYCLE_FRAMES):
        cycle = frame / CYCLE_FRAMES
        legs = stance_legs(cycle)
        pose_at(armature, cycle, 0.0)
        bpy.context.view_layer.update()

        if legs:
            planted[frame] = -sum(armature.pose.bones[lower].tail.z - armature.data.bones[lower].tail_local.z for lower in legs) / len(legs)

    return [planted.get(frame, flight_height(planted, frame)) for frame in range(CYCLE_FRAMES)]


def flight_height(planted: dict, frame: int) -> float:
    last = max(planted)
    first = min(planted) + CYCLE_FRAMES
    share = (frame - last) / (first - last)

    return planted[last] + (planted[first - CYCLE_FRAMES] - planted[last]) * share + 4.0 * SUSPENSION_LIFT * share * (1.0 - share)


def build_gallop(armature, name: str) -> bpy.types.Action:
    """New action with one key per frame on every bone (the last frame repeats the first, for a seamless loop)."""
    action = bpy.data.actions.new(name)
    armature.animation_data_create()
    armature.animation_data.action = action
    heights = trunk_heights(armature)

    for frame in range(CYCLE_FRAMES + 1):
        pose_at(armature, (frame % CYCLE_FRAMES) / CYCLE_FRAMES, heights[frame % CYCLE_FRAMES])
        key_pose(armature, frame + 1)

    for pose_bone in armature.pose.bones:
        pose_bone.rotation_quaternion = Quaternion()
        pose_bone.location = Vector()

    return action


def key_pose(armature, frame: int) -> None:
    for pose_bone in armature.pose.bones:
        pose_bone.keyframe_insert("rotation_quaternion", frame=frame)
        pose_bone.keyframe_insert("location", frame=frame)


def replace_run(armature, run_name: str) -> None:
    """Swap the pack's run (a loose canter) for the gallop, under the same action name. Call it once the bones
    stand where they are exported (the trunk height is measured on the final legs)."""
    old = bpy.data.actions[run_name]
    old.name = f"{run_name}_pack"
    build_gallop(armature, run_name)
    bpy.data.actions.remove(old)
    armature.animation_data.action = None


