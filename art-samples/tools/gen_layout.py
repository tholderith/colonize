"""Generates scene/layout.json: the shared harbor-town scene every engine renders."""
import json, math, os

W, H = 20, 20
def terrain(x, y):
    dx, dy = (x - 9.0) / 8.6, (y - 9.5) / 7.6
    d = math.hypot(dx, dy) + 0.07 * math.sin(x * 1.3 + 0.5) + 0.07 * math.cos(y * 1.7)
    if d < 0.74: return "G"
    if d < 0.93: return "B"
    if d < 1.18: return "S"
    return "D"

grid = [[terrain(x, y) for x in range(W)] for y in range(H)]
# main street (y=9, x=5..13) and harbour road (x=13, y=6..12)
for x in range(5, 14): grid[9][x] = "R"
for y in range(6, 13): grid[y][13] = "R"
for x in (14, 15): grid[11][x] = "R"   # spur to the pier

objects = []
FOOT = {"warehouse": (2, 2), "wheat_field": (2, 2), "ship": (2, 2), "chapel": (2, 2)}
def put(sprite, x, y, allowed="G"):
    fw, fh = FOOT.get(sprite, (1, 1))
    for i in range(fw):
        for j in range(fh):
            t = grid[y + j][x + i]
            assert t in allowed, f"{sprite}@{x},{y}: tile {x+i},{y+j} is {t}"
    objects.append({"sprite": sprite, "x": x, "y": y})

# farmland to the west
put("wheat_field", 4, 6); put("wheat_field", 6, 6); put("wheat_field", 4, 10)
put("farmhouse", 8, 6); put("windmill", 8, 7)
# town along the main street (y=9)
for x in (6, 7, 9, 10, 11, 12): put("house", x, 8)
for x in (6, 7, 8): put("house", x, 10)
for x in (6, 7, 8): put("house", x, 12)
put("chapel", 9, 10)
put("warehouse", 11, 10)
# forestry to the north-east
put("lumberjack", 11, 6)
for (x, y) in [(8, 4), (9, 5), (10, 5), (11, 5), (12, 5), (10, 6), (12, 6), (12, 7), (6, 5), (7, 5),
               (3, 12), (4, 13), (5, 13), (3, 13), (9, 12), (10, 13), (14, 7), (14, 13)]:
    put("tree", x, y, "GB")
put("rock", 8, 15, "GB"); put("rock", 15, 13, "GB"); put("rock", 3, 8, "GB")
# harbour
put("pier", 16, 11, "S")
put("ship", 17, 11, "SD")
put("ship", 2, 15, "SD")
# life
put("cart", 13, 8, "R"); put("cart", 10, 9, "R")
put("colonist", 7, 9, "R"); put("colonist", 13, 11, "R"); put("colonist", 15, 11, "R"); put("colonist", 5, 8)

keys = {"D": "deep_water", "S": "shallow_water", "B": "sand", "G": "grass", "R": "road"}
out = {
    "_doc": "See art-samples/SPEC.md. terrain[y] is a row string; char index = x.",
    "width": W, "height": H,
    "terrain_legend": keys,
    "terrain": ["".join(r) for r in grid],
    "objects": objects,
}
p = os.path.join(os.path.dirname(__file__), "..", "scene", "layout.json")
json.dump(out, open(p, "w"), indent=1)
print("\n".join(out["terrain"]))
