import sexpdata as s

TOLERANCE = 0.2


def cadr(x):
    return s.car(s.cdr(x))


def cddr(x):
    return s.cdr(s.cdr(x))


with open("../kicad/Digital Audio Switch.kicad_pcb", "r") as f:
    kicad_pcb = s.load(f)


# Assumes the board is cut out with a single rectangle
[rect] = [
    s.cdr(x)
    for x in kicad_pcb
    if s.car(x) == s.Symbol("gr_rect") and [s.Symbol("layer"), "Edge.Cuts"] in s.cdr(x)
]
[[start_x, start_y]] = [s.cdr(x) for x in rect if s.car(x) == s.Symbol("start")]
[[end_x, end_y]] = [s.cdr(x) for x in rect if s.car(x) == s.Symbol("end")]
[start_x, start_y, end_x, end_y] = [
    min(start_x, end_x),
    min(start_y, end_y),
    max(start_x, end_x),
    max(start_y, end_y),
]
width = end_x - start_x
height = end_y - start_y
print(
    f"""
pcb_width = {width};
pcb_height = {height};
    """.strip()
)

footprints = [
    s.cdr(x)
    for x in kicad_pcb
    if s.car(x) == s.Symbol("footprint") and s.car(s.cdr(x)).startswith("MountingHole:")
]

holes = []
for hole in footprints:
    [[hole_x, hole_y]] = [s.cdr(x) for x in hole if s.car(x) == s.Symbol("at")]
    pads = [cddr(x) for x in hole if s.car(x) == s.Symbol("pad")]
    for pad in pads:
        [[pad_x, pad_y]] = [s.cdr(x) for x in pad if s.car(x) == s.Symbol("at")]
        drills = [cadr(x) for x in pad if s.car(x) == s.Symbol("drill")]
        for diameter in drills:
            pos_x = (hole_x + pad_x) - start_x
            pos_y = (hole_y + pad_y) - start_y
            holes.append([pos_x, pos_y, diameter])

# Y coordinates are inverted between KiCad and OpenSCAD
print(f"drill_holes = {[[[x, -y + height], r] for x, y, r in holes]};")
