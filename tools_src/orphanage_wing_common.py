"""Measurements and helpers shared by the four wing halls of the orphanage (orphanage_wing_*.py).

Every wing hall is 29.1 m along the facade (u -14.55..14.55) and 23.8 m into the lot (d 0.3..24.1). A corridor runs
its whole length between two walls at d = 10.8 and d = 13.6, from the doorway of the vestibule to the window of the
far end wall: the front band (d 0.3..10.65) has the facade windows, the back band (d 13.75..24.1) the high windows
of the back wall (sill 3.3 m, so tall furniture may stand under them).
"""

WALL_HALF = 0.15  # half the thickness of an inner wall (WALL = 0.3 in build_town_houses.py)
HALL_LEFT = -14.55
HALL_RIGHT = 14.55
HALL_FRONT = 0.3
HALL_BACK = 24.1  # back face of a 25 m deep hall
CORRIDOR = (10.8, 13.6)  # d of the axes of the two corridor walls
FRONT_BAND = (HALL_FRONT, CORRIDOR[0] - WALL_HALF)  # (d from, d to) of the rooms on the facade
BACK_BAND = (CORRIDOR[1] + WALL_HALF, HALL_BACK)  # (d from, d to) of the rooms on the back wall
CORRIDOR_CLEAR = (CORRIDOR[0] + WALL_HALF, CORRIDOR[1] - WALL_HALF)  # (d from, d to) of the corridor floor
CORRIDOR_MIDDLE = sum(CORRIDOR) / 2.0
FACADE_PIERS = (1.81, 5.1375, 8.175, 11.2125)  # |u| of the facade piers between the windows (cross walls of the front band)
BACK_PIERS = ((-2.85, 2.85), (4.77, 6.86), (8.78, 10.88), (12.8, 14.4))  # |u| stretches of the back wall clear of its windows
DOOR = dict(width=1.2, height=2.4)  # an ordinary room door
WIDE_DOOR = dict(width=1.6, height=2.6)  # a double door (refectory, chapel, fencing hall)

CORRIDOR_FINISH = dict(dado="FFFFFF", trim="3A5E8C", material="azulejo", uv=("world", 1.2))  # blue and white tiles as in the vestibule


def door(at: float, kind: dict = None, **extra) -> dict:
    """A doorway of a partition centred at `at` along it (no leaf unless asked)."""
    return dict(at=at, **(kind or DOOR), **extra)


def hatch(at: float, width: float, sill: float = 0.95, height: float = 1.9) -> dict:
    """An opening with a sill in a partition (serving hatch, porter's window, parlour grille): no floor lane."""
    return dict(at=at, width=width, height=height, sill=sill, lane=())


def corridor_walls(front_rooms: list, back_rooms: list, corridor_finish: str) -> list:
    """Partitions of the two corridor walls, one stretch per room: rooms are (u from, u to, finish, [doors]) in
    order along u; the corridor face of every stretch gets corridor_finish."""
    front = [("d", CORRIDOR[0], u_from, u_to, dict(doors=doors, faces=(finish, corridor_finish))) for u_from, u_to, finish, doors in front_rooms]
    back = [("d", CORRIDOR[1], u_from, u_to, dict(doors=doors, faces=(corridor_finish, finish))) for u_from, u_to, finish, doors in back_rooms]

    return front + back


def cross_wall(u: float, band: tuple, low_finish: str, high_finish: str, doors: list = ()) -> tuple:
    """A wall across one band at u (from the facade or the back wall to the corridor wall)."""
    return ("u", u, band[0], band[1], dict(doors=list(doors), faces=(low_finish, high_finish)))


def bed_row(f, name: str, u_list: list, head_d: float, normal: int, locker: str = "night_table", **options) -> None:
    """Beds side by side with their heads at d = head_d (normal +1: the beds lie toward larger d), a locker beside the
    head of every bed on its +u side."""
    width, depth, _ = f.prop_size(name)
    locker_depth = f.prop_size(locker)[1] if locker else 0.0
    turn = 180.0 if normal > 0 else 0.0  # the head of a bed and the back of a locker are at +Y

    for bed_u in u_list:
        f.put(name, bed_u, head_d + normal * depth / 2.0, turn, **options)

        if locker:
            f.put(locker, bed_u + width / 2.0 + 0.27, head_d + normal * locker_depth / 2.0, turn)


def spaced(start: float, pitch: float, count: int) -> list:
    """count positions from start, pitch apart."""
    return [start + pitch * index for index in range(count)]
