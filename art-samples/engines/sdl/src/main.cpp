// colonize art-sample renderer, C++17 + SDL2 (SDL_Renderer).
//
//   colonize_sdl --style <dir> --out <png> [--layout <json>] [--renderer surface|<sdl-driver>]
//   colonize_sdl --style <dir>            (interactive window: arrows/WASD/drag pan, wheel zoom,
//                                          0 reset, F5 reload style, Esc quit)
//
// Headless renderers:
//   surface   (default) SDL software renderer drawing straight into an SDL_Surface.
//             Needs no display / X server at all.
//   opengl, opengles2, software, ...  any SDL render driver: hidden window + 1920x1080
//             target texture + SDL_RenderReadPixels. Needs a display (e.g. xvfb-run).
#include <SDL.h>
#include <SDL_image.h>

#include <chrono>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <map>
#include <string>

#include "scene.hpp"

static constexpr int W = 1920, H = 1080;

using Clock = std::chrono::steady_clock;
static double msSince(Clock::time_point t) {
    return std::chrono::duration<double, std::milli>(Clock::now() - t).count();
}

struct Tex {
    SDL_Texture* t = nullptr;
    int w = 0, h = 0;
};

struct Gfx {
    SDL_Renderer* r = nullptr;
    std::map<std::string, Tex> tex;

    void freeAll() {
        for (auto& kv : tex) SDL_DestroyTexture(kv.second.t);
        tex.clear();
    }

    // Load every image referenced by the scene. Always normalise to ARGB8888 first so
    // paletted / grey / 16-bit PNGs (e.g. pixel art with tRNS) behave like PIL's convert("RGBA").
    bool load(const Scene& sc) {
        for (const auto& c : sc.cmds) {
            if (tex.count(c.file)) continue;
            std::string path = sc.styleDir + "/" + c.file;
            SDL_Surface* raw = IMG_Load(path.c_str());
            if (!raw) {
                std::fprintf(stderr, "error: IMG_Load(%s): %s\n", path.c_str(), IMG_GetError());
                return false;
            }
            SDL_Surface* s = SDL_ConvertSurfaceFormat(raw, SDL_PIXELFORMAT_ARGB8888, 0);
            SDL_FreeSurface(raw);
            if (!s) {
                std::fprintf(stderr, "error: convert %s: %s\n", path.c_str(), SDL_GetError());
                return false;
            }
            Tex t;
            t.t = SDL_CreateTextureFromSurface(r, s);
            t.w = s->w;
            t.h = s->h;
            SDL_FreeSurface(s);
            if (!t.t) {
                std::fprintf(stderr, "error: texture %s: %s\n", path.c_str(), SDL_GetError());
                return false;
            }
            SDL_SetTextureBlendMode(t.t, SDL_BLENDMODE_BLEND);  // straight-alpha "over"
            SDL_SetTextureScaleMode(t.t, sc.nearest ? SDL_ScaleModeNearest : SDL_ScaleModeLinear);
            tex[c.file] = t;
        }
        return true;
    }

    // World commands are transformed by pan/zoom (zoom about the screen centre);
    // overlays are drawn 1:1 in screen space.
    void draw(const Scene& sc, float panX = 0, float panY = 0, float zoom = 1) {
        SDL_SetRenderDrawBlendMode(r, SDL_BLENDMODE_NONE);
        SDL_SetRenderDrawColor(r, sc.bg[0], sc.bg[1], sc.bg[2], 255);
        SDL_RenderClear(r);
        const bool identity = panX == 0 && panY == 0 && zoom == 1;
        for (const auto& c : sc.cmds) {
            const Tex& t = tex.at(c.file);
            if (!c.world || identity) {
                SDL_Rect d{c.x, c.y, t.w, t.h};  // exact integer 1:1 blit
                SDL_RenderCopy(r, t.t, nullptr, &d);
            } else {
                SDL_FRect d{(c.x - W / 2.f) * zoom + W / 2.f + panX, (c.y - H / 2.f) * zoom + H / 2.f + panY,
                            t.w * zoom, t.h * zoom};
                SDL_RenderCopyF(r, t.t, nullptr, &d);
            }
        }
    }
};

static bool savePNG(SDL_Surface* argb, const std::string& out) {
    // Reference saves RGB (alpha dropped); do the same.
    SDL_Surface* rgb = SDL_ConvertSurfaceFormat(argb, SDL_PIXELFORMAT_RGB24, 0);
    if (!rgb) return false;
    int rc = IMG_SavePNG(rgb, out.c_str());
    SDL_FreeSurface(rgb);
    if (rc != 0) std::fprintf(stderr, "error: IMG_SavePNG(%s): %s\n", out.c_str(), IMG_GetError());
    return rc == 0;
}

static int renderHeadless(const std::string& style, const std::string& layout, const std::string& out,
                          const std::string& driver) {
    auto t0 = Clock::now();
    Scene sc = loadScene(style, layout);
    double tParse = msSince(t0);

    SDL_Window* win = nullptr;
    SDL_Texture* target = nullptr;
    SDL_Surface* canvas = SDL_CreateRGBSurfaceWithFormat(0, W, H, 32, SDL_PIXELFORMAT_ARGB8888);
    Gfx g;
    if (driver == "surface") {
        if (SDL_Init(0) != 0) return std::fprintf(stderr, "SDL_Init: %s\n", SDL_GetError()), 1;
        g.r = SDL_CreateSoftwareRenderer(canvas);
    } else {
        SDL_SetHint(SDL_HINT_RENDER_DRIVER, driver.c_str());
        if (SDL_Init(SDL_INIT_VIDEO) != 0)
            return std::fprintf(stderr, "SDL_Init(VIDEO): %s (need a display; try xvfb-run)\n", SDL_GetError()), 1;
        win = SDL_CreateWindow("colonize_sdl (offscreen)", 0, 0, 64, 64, SDL_WINDOW_HIDDEN);
        if (!win) return std::fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError()), 1;
        g.r = SDL_CreateRenderer(win, -1, SDL_RENDERER_TARGETTEXTURE);
        if (g.r) {
            target = SDL_CreateTexture(g.r, SDL_PIXELFORMAT_ARGB8888, SDL_TEXTUREACCESS_TARGET, W, H);
            if (!target || SDL_SetRenderTarget(g.r, target) != 0)
                return std::fprintf(stderr, "render target: %s\n", SDL_GetError()), 1;
        }
    }
    if (!g.r) return std::fprintf(stderr, "renderer: %s\n", SDL_GetError()), 1;
    SDL_RendererInfo info;
    SDL_GetRendererInfo(g.r, &info);

    auto t1 = Clock::now();
    if (!g.load(sc)) return 1;
    double tLoad = msSince(t1);

    auto t2 = Clock::now();
    g.draw(sc);
    if (target) {
        if (SDL_RenderReadPixels(g.r, nullptr, SDL_PIXELFORMAT_ARGB8888, canvas->pixels, canvas->pitch) != 0)
            return std::fprintf(stderr, "SDL_RenderReadPixels: %s\n", SDL_GetError()), 1;
    } else {
        SDL_RenderPresent(g.r);  // flush the software renderer into `canvas`
    }
    double tDraw = msSince(t2);

    auto t3 = Clock::now();
    bool ok = savePNG(canvas, out);
    double tSave = msSince(t3);

    std::fprintf(stderr,
                 "style '%s' via SDL '%s' renderer (video driver: %s): %zu draws | parse %.1f ms, "
                 "load %.1f ms, draw+readback %.1f ms, png %.1f ms -> %s\n",
                 sc.name.c_str(), info.name, win ? SDL_GetCurrentVideoDriver() : "none", sc.cmds.size(),
                 tParse, tLoad, tDraw, tSave, out.c_str());

    g.freeAll();
    if (target) SDL_DestroyTexture(target);
    SDL_DestroyRenderer(g.r);
    if (win) SDL_DestroyWindow(win);
    SDL_FreeSurface(canvas);
    SDL_Quit();
    return ok ? 0 : 1;
}

static int runInteractive(const std::string& style, const std::string& layout, int maxFrames) {
    Scene sc = loadScene(style, layout);
    if (SDL_Init(SDL_INIT_VIDEO) != 0) return std::fprintf(stderr, "SDL_Init: %s\n", SDL_GetError()), 1;
    SDL_Window* win = SDL_CreateWindow(("Colonize art sample - " + sc.name).c_str(), SDL_WINDOWPOS_CENTERED,
                                       SDL_WINDOWPOS_CENTERED, 1280, 720,
                                       SDL_WINDOW_RESIZABLE | SDL_WINDOW_ALLOW_HIGHDPI);
    if (!win) return std::fprintf(stderr, "SDL_CreateWindow: %s\n", SDL_GetError()), 1;
    Gfx g;
    g.r = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED | SDL_RENDERER_PRESENTVSYNC);
    if (!g.r) g.r = SDL_CreateRenderer(win, -1, 0);
    if (!g.r) return std::fprintf(stderr, "renderer: %s\n", SDL_GetError()), 1;
    SDL_RenderSetLogicalSize(g.r, W, H);  // UI overlays are authored for 1920x1080
    if (!g.load(sc)) return 1;

    float panX = 0, panY = 0, zoom = 1;
    bool dragging = false, running = true;
    auto last = Clock::now();
    for (int frame = 0; running && (maxFrames <= 0 || frame < maxFrames); frame++) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            switch (e.type) {
                case SDL_QUIT: running = false; break;
                case SDL_KEYDOWN:
                    if (e.key.keysym.sym == SDLK_ESCAPE) running = false;
                    if (e.key.keysym.sym == SDLK_0) panX = panY = 0, zoom = 1;
                    if (e.key.keysym.sym == SDLK_F5) {  // hot-reload the style folder
                        try {
                            Scene n = loadScene(style, layout);
                            g.freeAll();
                            sc = n;
                            if (!g.load(sc)) running = false;
                            SDL_SetWindowTitle(win, ("Colonize art sample - " + sc.name).c_str());
                        } catch (const std::exception& ex) {
                            std::fprintf(stderr, "reload failed: %s\n", ex.what());
                        }
                    }
                    break;
                case SDL_MOUSEBUTTONDOWN: dragging = true; break;
                case SDL_MOUSEBUTTONUP: dragging = false; break;
                case SDL_MOUSEMOTION:  // logical-size mode already maps to 1920x1080 coords
                    if (dragging) panX += e.motion.xrel, panY += e.motion.yrel;
                    break;
                case SDL_MOUSEWHEEL: {
                    float nz = std::fmin(3.f, std::fmax(0.25f, zoom * (e.wheel.y > 0 ? 1.1f : 1 / 1.1f)));
                    panX *= nz / zoom, panY *= nz / zoom, zoom = nz;
                    break;
                }
            }
        }
        float dt = float(msSince(last) / 1000.0);
        last = Clock::now();
        const Uint8* k = SDL_GetKeyboardState(nullptr);
        float sp = 900 * dt;
        if (k[SDL_SCANCODE_LEFT] || k[SDL_SCANCODE_A]) panX += sp;
        if (k[SDL_SCANCODE_RIGHT] || k[SDL_SCANCODE_D]) panX -= sp;
        if (k[SDL_SCANCODE_UP] || k[SDL_SCANCODE_W]) panY += sp;
        if (k[SDL_SCANCODE_DOWN] || k[SDL_SCANCODE_S]) panY -= sp;
        g.draw(sc, std::round(panX), std::round(panY), zoom);
        SDL_RenderPresent(g.r);
    }
    g.freeAll();
    SDL_DestroyRenderer(g.r);
    SDL_DestroyWindow(win);
    SDL_Quit();
    return 0;
}

static void usage() {
    std::fprintf(stderr,
                 "usage: colonize_sdl --style <style-dir> [--out <png>] [--layout <layout.json>]\n"
                 "                    [--renderer surface|opengl|opengles2|software] [--frames N]\n"
                 "  with --out: render 1920x1080 headless and exit (default renderer 'surface',\n"
                 "              no display needed). Without --out: interactive window.\n");
}

int main(int argc, char** argv) {
    std::string style, out, layout, driver = "surface";
    int frames = 0;
    for (int i = 1; i < argc; i++) {
        std::string a = argv[i];
        auto next = [&]() -> std::string {
            if (i + 1 >= argc) usage(), std::exit(2);
            return argv[++i];
        };
        if (a == "--style") style = next();
        else if (a == "--out") out = next();
        else if (a == "--layout") layout = next();
        else if (a == "--renderer") driver = next();
        else if (a == "--frames") frames = std::stoi(next());
        else if (a == "-h" || a == "--help") return usage(), 0;
        else return usage(), 2;
    }
    if (style.empty()) return usage(), 2;
    while (style.size() > 1 && style.back() == '/') style.pop_back();
    if (layout.empty()) layout = defaultLayoutPath(style);

    if (IMG_Init(IMG_INIT_PNG) == 0) std::fprintf(stderr, "IMG_Init: %s\n", IMG_GetError());
    try {
        int rc = out.empty() ? runInteractive(style, layout, frames) : renderHeadless(style, layout, out, driver);
        IMG_Quit();
        return rc;
    } catch (const std::exception& e) {
        std::fprintf(stderr, "error: %s\n", e.what());
        return 1;
    }
}
