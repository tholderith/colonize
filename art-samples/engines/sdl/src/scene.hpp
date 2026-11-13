// Scene loading + draw-list construction (engine-agnostic: no SDL here).
// Implements art-samples/SPEC.md; tools/render_ref.py is the source of truth.
#pragma once
#include <string>
#include <vector>
#include <cstdint>

struct SpriteDef {
    std::vector<std::string> files;  // relative to style dir
    int ax = 0, ay = 0;              // anchor
    bool flat = false;
};

struct Overlay {
    std::string file;
    int x = 0, y = 0;  // pos - anchor (top-left)
};

// One blit: draw image `file` with its top-left at (x, y) in 1920x1080 scene space.
struct DrawCmd {
    std::string file;
    int x, y;
    bool world;  // true = scrolls with camera, false = screen-space overlay
};

struct Scene {
    std::string styleDir;
    std::string name;
    uint8_t bg[4] = {0, 0, 0, 255};
    bool nearest = false;            // manifest "filter": "nearest"
    std::vector<DrawCmd> cmds;       // already in final draw order
};

// Throws std::runtime_error on malformed input.
Scene loadScene(const std::string& styleDir, const std::string& layoutPath);

// Default layout path for a style dir: <style>/../../scene/layout.json if it exists,
// otherwise the path baked in at compile time.
std::string defaultLayoutPath(const std::string& styleDir);
