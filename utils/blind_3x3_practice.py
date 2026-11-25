#!/usr/bin/env python3
"""Generate a random-move 3x3 scramble and Speffz sticker cycles.

The cube starts in the standard Speffz orientation: U on top, D on bottom,
and F in front. Default buffers are edge B (UR) and corner A (UBL).
This uses the standard Speffz sticker order and reports edge and corner
cycles on separate lines, with a space between cycles.
"""
import argparse
import random
from collections import deque
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from PIL import Image, ImageDraw

# A facelet is (cubie coordinate, outward normal). Coordinates use x=R,
# y=U, z=F. These face orders are standard Speffz, clockwise as viewed.
EDGE_FACELETS = {
    "U": [(0, 1, -1), (1, 1, 0), (0, 1, 1), (-1, 1, 0)],
    "L": [(-1, 1, 0), (-1, 0, 1), (-1, -1, 0), (-1, 0, -1)],
    "F": [(0, 1, 1), (1, 0, 1), (0, -1, 1), (-1, 0, 1)],
    "R": [(1, 1, 0), (1, 0, -1), (1, -1, 0), (1, 0, 1)],
    "B": [(0, 1, -1), (-1, 0, -1), (0, -1, -1), (1, 0, -1)],
    "D": [(0, -1, 1), (1, -1, 0), (0, -1, -1), (-1, -1, 0)],
}
CORNER_FACELETS = {
    "U": [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)],
    "L": [(-1, 1, -1), (-1, 1, 1), (-1, -1, 1), (-1, -1, -1)],
    "F": [(-1, 1, 1), (1, 1, 1), (1, -1, 1), (-1, -1, 1)],
    "R": [(1, 1, 1), (1, 1, -1), (1, -1, -1), (1, -1, 1)],
    "B": [(1, 1, -1), (-1, 1, -1), (-1, -1, -1), (1, -1, -1)],
    "D": [(-1, -1, 1), (1, -1, 1), (1, -1, -1), (-1, -1, -1)],
}
NORMALS = {"U": (0, 1, 0), "D": (0, -1, 0), "R": (1, 0, 0),
           "L": (-1, 0, 0), "F": (0, 0, 1), "B": (0, 0, -1)}
COLORS = {"U": "#ffffff", "D": "#fff200", "F": "#00d948",
          "B": "#2563eb", "R": "#dc2626", "L": "#f97316"}


def facelets(groups):
    result = {}
    letter = ord("A")
    for face in "ULFRBD":
        normal = NORMALS[face]
        for position in groups[face]:
            result[chr(letter)] = (position, normal)
            letter += 1
    return result


def rotate_vec(v, axis, quarter):
    """Rotate by quarter (+1 is +90 degrees) around a positive axis."""
    x, y, z = v
    for _ in range(quarter % 4):
        if axis == "x":
            x, y, z = x, -z, y
        elif axis == "y":
            x, y, z = z, y, -x
        else:
            x, y, z = -y, x, z
    return x, y, z


def apply_move(state, move):
    face = move[0].upper()
    wide = move[0].islower()
    suffix = move[1:] 
    turns = {"": 1, "'": 3, "2": 2}[suffix]
    axis = {"U": "y", "D": "y", "R": "x", "L": "x", "F": "z", "B": "z"}[face]
    # Clockwise from outside is -90 about the outward normal.
    sign = -1 if face in "URF" else 1
    q = sign * turns
    layer = NORMALS[face]
    for letter, (pos, normal) in tuple(state.items()):
        depth = sum(pos[i] * layer[i] for i in range(3))
        if depth == 1 or (wide and depth == 0):
            state[letter] = (rotate_vec(pos, axis, q), rotate_vec(normal, axis, q))


def random_scramble(length, rng):
    faces = "UDLRFB"
    result, previous = [], None
    for _ in range(length):
        face = rng.choice([f for f in faces if f != previous])
        result.append(face + rng.choice(("", "'", "2")))
        previous = face
    return result


def orientation_steps(scramble):
    """Whole-cube rotations needed to restore white U, green F, red R."""
    centers = {face: (normal, normal) for face, normal in NORMALS.items()}
    for move in scramble:
        apply_move(centers, move)
    orientation = tuple(centers[face][1] for face in ("U", "F", "R"))
    target = tuple(NORMALS[face] for face in ("U", "F", "R"))
    queue = deque([(orientation, ())])
    seen = {orientation}
    while queue:
        current, steps = queue.popleft()
        if current == target:
            return steps
        for axis in "xyz":
            next_orientation = tuple(rotate_vec(v, axis, 1) for v in current)
            if next_orientation not in seen:
                seen.add(next_orientation)
                queue.append((next_orientation, steps + (axis,)))
    raise ValueError("center orientation could not be restored")


def reorient_location(location, steps):
    pos, normal = location
    for axis in steps:
        pos = rotate_vec(pos, axis, 1)
        normal = rotate_vec(normal, axis, 1)
    return pos, normal


def cycles(groups, buffer, scramble):
    state = facelets(groups)
    for move in scramble:
        apply_move(state, move)
    steps = orientation_steps(scramble)
    state = {letter: reorient_location(location, steps)
             for letter, location in state.items()}
    initial = facelets(groups)
    location_letter = {location: letter for letter, location in initial.items()}
    # Map each sticker letter to the letter at the position it moves into.
    permutation = {letter: location_letter[location]
                   for letter, location in state.items()}
    piece = {letter: location[0] for letter, location in initial.items()}
    # The sticker occupying the buffer position is the first target when the
    # buffer contains a different piece.
    occupant = {destination: source for source, destination in permutation.items()}
    first = occupant[buffer]
    visited_pieces = {piece[buffer]}
    result = []
    starts = ([first] if piece[first] != piece[buffer] else []) + list(initial)
    for start in starts:
        if piece[start] in visited_pieces:
            continue
        cycle, current = [], start
        while piece[current] not in visited_pieces:
            visited_pieces.add(piece[current])
            cycle.append(current)
            current = occupant[current]
        if len(cycle) > 1 or permutation[start] != start:
            if piece[current] != piece[buffer]:
                cycle.append(current)
            result.append(cycle)
    return result


def format_cycles(cycle_list):
    return " ".join("".join(cycle) for cycle in cycle_list) or "(solved)"


def scrambled_stickers(scramble):
    """Return colors reoriented to white U, green F, red R, with fixed letters."""
    stickers = {}
    for groups in (EDGE_FACELETS, CORNER_FACELETS):
        initial = facelets(groups)
        state = initial.copy()
        for move in scramble:
            apply_move(state, move)
        for letter, location in state.items():
            stickers[location] = COLORS["ULFRBD"[(ord(letter) - ord("A")) // 4]]
    centers = {face: (normal, normal) for face, normal in NORMALS.items()}
    for move in scramble:
        apply_move(centers, move)
    for face, location in centers.items():
        stickers[location] = COLORS[face]

    steps = orientation_steps(scramble)
    position_letters = {}
    for groups in (EDGE_FACELETS, CORNER_FACELETS):
        position_letters.update({location: letter
                                 for letter, location in facelets(groups).items()})
    return {new_location: (color, position_letters.get(new_location))
            for location, color in stickers.items()
            for new_location in (reorient_location(location, steps),)}


def sticker_position(face, row, col):
    if face == "U":
        return (col - 1, 1, row - 1)
    if face == "F":
        return (col - 1, 1 - row, 1)
    return (1, 1 - row, 1 - col)  # R: left-to-right runs F to B


def draw_cube(scramble, path):
    """Save an isometric PNG showing the U, F, and R faces."""
    stickers = scrambled_stickers(scramble)
    image = Image.new("RGBA", (1300, 530), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    x_offset = -70
    faces = {
        "U": ((300, 40), (490, 150), (300, 260), (110, 150)),
        "F": ((110, 150), (300, 260), (300, 480), (110, 370)),
        "R": ((300, 260), (490, 150), (490, 370), (300, 480)),
    }
    outline = [(x + x_offset, y) for x, y in
               ((300, 40), (490, 150), (490, 370),
                (300, 480), (110, 370), (110, 150))]
    draw.polygon(outline, fill="#172033")

    def point(quad, row, col):
        tl, tr, br, bl = quad
        u, v = col / 3, row / 3
        return (x_offset + round((1-u)*(1-v)*tl[0] + u*(1-v)*tr[0] + u*v*br[0] + (1-u)*v*bl[0]),
                round((1-u)*(1-v)*tl[1] + u*(1-v)*tr[1] + u*v*br[1] + (1-u)*v*bl[1]))

    for face in ("U", "F", "R"):
        quad = faces[face]
        for row in range(3):
            for col in range(3):
                position = sticker_position(face, row, col)
                color, _ = stickers[(position, NORMALS[face])]
                polygon = [point(quad, row, col), point(quad, row, col+1),
                           point(quad, row+1, col+1), point(quad, row+1, col)]
                draw.polygon(polygon, fill=color, outline="#172033", width=5)
    draw.line(outline + [outline[0]], fill="#172033", width=5, joint="curve")
    image.save(path, format="PNG")


@dataclass(frozen=True)
class Practice:
    seed: int | None
    scramble: str
    edges: str
    corners: str
    image: bytes
    content: str


def generate_practice(scramble: str | None = None, seed: int | None = None,
                      *, length: int = 20, edge_buffer: str = "B",
                      corner_buffer: str = "A") -> Practice:
    """Create one scramble, both Speffz traces, and its PNG image."""
    if scramble is None:
        seed = seed if seed is not None else random.SystemRandom().getrandbits(64)
        moves = random_scramble(length, random.Random(seed))
    else:
        moves = scramble.split()
        seed = None

    scramble_text = " ".join(moves)
    edges = format_cycles(cycles(EDGE_FACELETS, edge_buffer.upper(), moves))
    corners = format_cycles(cycles(CORNER_FACELETS, corner_buffer.upper(), moves))
    image_buffer = BytesIO()
    draw_cube(moves, image_buffer)
    seed_line = f"Seed: {seed}\n" if seed is not None else ""
    content = (f"{seed_line}Scramble: {scramble_text}\n"
               f"Edges: {edges}\nCorners: {corners}")
    return Practice(seed, scramble_text, edges, corners,
                    image_buffer.getvalue(), content)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--length", type=int, default=20, help="random-move count (default: 20)")
    parser.add_argument("--edge-buffer", default="B", help="edge buffer sticker A-X (default B / UR)")
    parser.add_argument("--corner-buffer", default="A", help="corner buffer sticker A-X (default A / UBL)")
    parser.add_argument("--seed", type=int, help="optional random seed for repeatable practice")
    parser.add_argument("--scramble", help="quoted scramble string; lowercase r l u d f b are wide moves")
    parser.add_argument("--image", default="scrambled_cube.png",
                        help="output PNG path (default: scrambled_cube.png)")
    args = parser.parse_args()
    if args.length < 1:
        parser.error("--length must be at least 1")
    for kind, value in (("edge", args.edge_buffer), ("corner", args.corner_buffer)):
        if len(value) != 1 or value.upper() not in "ABCDEFGHIJKLMNOPQRSTUVWX":
            parser.error(f"--{kind}-buffer must be a letter from A to X")
    result = generate_practice(args.scramble, args.seed, length=args.length,
                               edge_buffer=args.edge_buffer,
                               corner_buffer=args.corner_buffer)
    print(result.content)
    Path(args.image).write_bytes(result.image)
    print(f"\nCube image (white top, green left, red right): {args.image}")

if __name__ == "__main__":
    main()
