#include "scene.hpp"

#include <algorithm>
#include <cstdio>
#include <fstream>
#include <map>
#include <stdexcept>
#include <tuple>

#include "nlohmann/json.hpp"

using json = nlohmann::json;

#ifndef ART_SAMPLES_DIR
#define ART_SAMPLES_DIR "."
#endif

static json readJson(const std::string& path) {
    std::ifstream f(path);
    if (!f) throw std::runtime_error("cannot open " + path);
    try {
        return json::parse(f);
    } catch (const std::exception& e) {
        throw std::runtime_error(path + ": " + e.what());
    }
}

static bool fileExists(const std::string& p) { return std::ifstream(p).good(); }

std::string defaultLayoutPath(const std::string& styleDir) {
    std::string rel = styleDir + "/../../scene/layout.json";
    if (fileExists(rel)) return rel;
    return std::string(ART_SAMPLES_DIR) + "/scene/layout.json";
}

static int hexNib(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    throw std::runtime_error(std::string("bad hex digit '") + c + "'");
}

// "#rgb", "#rrggbb", "#rrggbbaa". Alpha is parsed but the canvas is treated as opaque
// (the reference flattens with convert("RGB") at the end).
static void parseColor(const std::string& s, uint8_t out[4]) {
    if (s.empty() || s[0] != '#') throw std::runtime_error("background must be #hex: " + s);
    std::string h = s.substr(1);
    if (h.size() == 3) {
        for (int i = 0; i < 3; i++) out[i] = uint8_t(hexNib(h[i]) * 17);
        out[3] = 255;
    } else if (h.size() == 6 || h.size() == 8) {
        for (size_t i = 0; i < h.size() / 2; i++)
            out[i] = uint8_t(hexNib(h[2 * i]) * 16 + hexNib(h[2 * i + 1]));
        if (h.size() == 6) out[3] = 255;
    } else {
        throw std::runtime_error("bad colour " + s);
    }
}

// Footprints are fixed by the spec table (same as render_ref.py's FOOT).
static void footprint(const std::string& key, int& fw, int& fh) {
    static const std::map<std::string, std::pair<int, int>> FOOT = {
        {"warehouse", {2, 2}}, {"wheat_field", {2, 2}}, {"ship", {2, 2}}, {"chapel", {2, 2}}};
    auto it = FOOT.find(key);
    fw = it == FOOT.end() ? 1 : it->second.first;
    fh = it == FOOT.end() ? 1 : it->second.second;
}

// South corner of tile (x, y).
static void south(int x, int y, int& sx, int& sy) {
    sx = 960 + (x - y) * 64;
    sy = -72 + (x + y) * 32 + 64;
}

Scene loadScene(const std::string& styleDir, const std::string& layoutPath) {
    Scene sc;
    sc.styleDir = styleDir;
    json m = readJson(styleDir + "/manifest.json");
    json lay = readJson(layoutPath);

    sc.name = m.value("name", std::string("?"));
    parseColor(m.value("background", std::string("#000000")), sc.bg);
    sc.nearest = m.value("filter", std::string("linear")) == "nearest";

    std::map<std::string, SpriteDef> sprites;
    for (auto& [key, s] : m.at("sprites").items()) {
        SpriteDef d;
        for (auto& f : s.at("files")) d.files.push_back(f.get<std::string>());
        if (d.files.empty()) throw std::runtime_error("sprite " + key + " has no files");
        d.ax = s.at("anchor").at(0).get<int>();
        d.ay = s.at("anchor").at(1).get<int>();
        d.flat = s.value("flat", false);
        sprites[key] = d;
    }

    auto emit = [&](const std::string& key, int x, int y, int px, int py) {
        auto it = sprites.find(key);
        if (it == sprites.end()) {
            std::fprintf(stderr, "warning: style has no sprite '%s' (skipped)\n", key.c_str());
            return;
        }
        const SpriteDef& d = it->second;
        const std::string& f = d.files[size_t((x * 7 + y * 13) % int(d.files.size()))];
        sc.cmds.push_back({f, px - d.ax, py - d.ay, true});
    };

    // 2. terrain, by (x+y, x)
    const int W = lay.at("width").get<int>(), H = lay.at("height").get<int>();
    const json& legend = lay.at("terrain_legend");
    const json& rows = lay.at("terrain");
    for (int d = 0; d <= W + H - 2; d++) {
        for (int x = 0; x < W; x++) {
            int y = d - x;
            if (y < 0 || y >= H) continue;
            std::string ch(1, rows.at(y).get<std::string>().at(size_t(x)));
            int px, py;
            south(x, y, px, py);
            emit(legend.at(ch).get<std::string>(), x, y, px, py);
        }
    }

    // 3./4. objects
    struct Obj { std::string key; int x, y, ax, ay, idx; };
    std::vector<Obj> flat, rest;
    int idx = 0;
    for (auto& o : lay.at("objects")) {
        Obj ob{o.at("sprite").get<std::string>(), o.at("x").get<int>(), o.at("y").get<int>(), 0, 0, idx++};
        int fw, fh;
        footprint(ob.key, fw, fh);
        ob.ax = ob.x + fw - 1;
        ob.ay = ob.y + fh - 1;
        auto it = sprites.find(ob.key);
        (it != sprites.end() && it->second.flat ? flat : rest).push_back(ob);
    }
    std::stable_sort(rest.begin(), rest.end(), [](const Obj& a, const Obj& b) {
        return std::make_tuple(a.ax + a.ay, a.ax, a.idx) < std::make_tuple(b.ax + b.ay, b.ax, b.idx);
    });
    for (auto* list : {&flat, &rest})
        for (auto& o : *list) {
            int px, py;
            south(o.ax, o.ay, px, py);
            emit(o.key, o.x, o.y, px, py);
        }

    // 5. overlays (screen space)
    if (m.contains("overlays"))
        for (auto& ov : m["overlays"]) {
            int ax = 0, ay = 0;
            if (ov.contains("anchor")) {
                ax = ov["anchor"].at(0).get<int>();
                ay = ov["anchor"].at(1).get<int>();
            }
            sc.cmds.push_back({ov.at("file").get<std::string>(), ov.at("pos").at(0).get<int>() - ax,
                               ov.at("pos").at(1).get<int>() - ay, false});
        }
    return sc;
}
