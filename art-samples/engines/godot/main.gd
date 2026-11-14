extends Node2D
## Renders art-samples/scene/layout.json with any style folder, loaded at runtime.
## Usage: godot --path <project> -- --style <abs style dir> --out <png> [--layout <json>] [--no-quit]
## Semantics follow SPEC.md / tools/render_ref.py exactly.

const FOOT := {"warehouse": Vector2i(2, 2), "wheat_field": Vector2i(2, 2),
		"ship": Vector2i(2, 2), "chapel": Vector2i(2, 2)}

var manifest: Dictionary
var style_dir: String
var tex_cache := {}


func _ready() -> void:
	var args := _parse_args(OS.get_cmdline_user_args())
	var project_dir := ProjectSettings.globalize_path("res://")
	style_dir = args.get("style", project_dir.path_join("../../styles/placeholder")).simplify_path()
	var layout_path: String = args.get("layout", project_dir.path_join("../../scene/layout.json")).simplify_path()

	manifest = _load_json(style_dir.path_join("manifest.json"))
	var layout := _load_json(layout_path)
	if manifest.is_empty() or layout.is_empty():
		get_tree().quit(1)
		return

	RenderingServer.set_default_clear_color(Color.html(manifest["background"]))
	texture_filter = (CanvasItem.TEXTURE_FILTER_NEAREST if manifest.get("filter", "linear") == "nearest"
			else CanvasItem.TEXTURE_FILTER_LINEAR)
	_build_scene(layout)

	if args.has("out"):
		# Let a couple of frames render, then grab the framebuffer.
		for i in 3:
			await RenderingServer.frame_post_draw
		var img := get_viewport().get_texture().get_image()
		img.convert(Image.FORMAT_RGB8)
		var err := img.save_png(args["out"])
		print("saved %s (%dx%d) err=%d" % [args["out"], img.get_width(), img.get_height(), err])
		get_tree().quit(0 if err == OK else 1)


func _build_scene(layout: Dictionary) -> void:
	var legend: Dictionary = layout["terrain_legend"]
	var rows: Array = layout["terrain"]
	# 1) terrain ordered by (x+y, x)
	var tiles: Array[Vector2i] = []
	for y in int(layout["height"]):
		for x in int(layout["width"]):
			tiles.append(Vector2i(x, y))
	tiles.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return a.x + a.y < b.x + b.y or (a.x + a.y == b.x + b.y and a.x < b.x))
	for t in tiles:
		_place(legend[rows[t.y][t.x]], t.x, t.y, _south(t))

	# 1b) world-space underlays in manifest order, after terrain and before objects
	for ul in manifest.get("underlays", []):
		var ua: Array = ul.get("anchor", [0, 0])
		var us := Sprite2D.new()
		us.texture = _tex(ul["file"])
		us.centered = false
		us.position = Vector2(ul["pos"][0] - ua[0], ul["pos"][1] - ua[1])
		add_child(us)

	# 2) flat objects in layout order, 3) the rest depth-sorted (index makes it stable)
	var flat := []
	var rest := []
	var objs: Array = layout["objects"]
	for i in objs.size():
		var o: Dictionary = objs[i]
		var e := {"i": i, "key": o["sprite"], "x": int(o["x"]), "y": int(o["y"]), "a": _anchor_tile(o)}
		if manifest["sprites"][o["sprite"]].get("flat", false):
			flat.append(e)
		else:
			rest.append(e)
	rest.sort_custom(func(p: Dictionary, q: Dictionary) -> bool:
		var dp: int = p.a.x + p.a.y
		var dq: int = q.a.x + q.a.y
		if dp != dq: return dp < dq
		if p.a.x != q.a.x: return p.a.x < q.a.x
		return p.i < q.i)
	for e in flat + rest:
		_place(e.key, e.x, e.y, _south(e.a))

	# 4) screen-space overlays in manifest order
	var ui := CanvasLayer.new()
	ui.name = "UI"
	add_child(ui)
	for ov in manifest.get("overlays", []):
		var a: Array = ov.get("anchor", [0, 0])
		var tr := TextureRect.new()
		tr.texture = _tex(ov["file"])
		tr.position = Vector2(ov["pos"][0] - a[0], ov["pos"][1] - a[1])
		tr.texture_filter = texture_filter
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		ui.add_child(tr)


func _place(key: String, x: int, y: int, p: Vector2i) -> void:
	var s: Dictionary = manifest["sprites"][key]
	var files: Array = s["files"]
	var spr := Sprite2D.new()
	spr.texture = _tex(files[(x * 7 + y * 13) % files.size()])
	spr.centered = false
	spr.position = Vector2(p.x - int(s["anchor"][0]), p.y - int(s["anchor"][1]))
	add_child(spr)  # tree order == draw order


func _south(t: Vector2i) -> Vector2i:
	return Vector2i(960 + (t.x - t.y) * 64, -72 + (t.x + t.y) * 32 + 64)


func _anchor_tile(o: Dictionary) -> Vector2i:
	var f: Vector2i = FOOT.get(o["sprite"], Vector2i.ONE)
	return Vector2i(int(o["x"]) + f.x - 1, int(o["y"]) + f.y - 1)


func _tex(file: String) -> Texture2D:
	if not tex_cache.has(file):
		var img := Image.load_from_file(style_dir.path_join(file))
		if img == null:
			push_error("cannot load " + file)
			img = Image.create(1, 1, false, Image.FORMAT_RGBA8)
		tex_cache[file] = ImageTexture.create_from_image(img)
	return tex_cache[file]


func _load_json(path: String) -> Dictionary:
	var text := FileAccess.get_file_as_string(path)
	var data = JSON.parse_string(text)
	if typeof(data) != TYPE_DICTIONARY:
		push_error("cannot parse JSON: " + path)
		return {}
	return data


func _parse_args(argv: PackedStringArray) -> Dictionary:
	var out := {}
	var i := 0
	while i < argv.size():
		if argv[i].begins_with("--") and i + 1 < argv.size() and not argv[i + 1].begins_with("--"):
			out[argv[i].substr(2)] = argv[i + 1]
			i += 2
		else:
			out[argv[i].substr(2)] = true
			i += 1
	return out
