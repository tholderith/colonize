"""Title key art: perspective night scene of a small colony built from the existing models. Usage: blender -b --python title.py -- [W H samples]
Writes $NWORK/title_raw.png (post: title_post.py -> public/assets/ui/title.png)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
import lib
import models as MD

def place(fn, args, wx, wy, rot=0.0, pivot=(0, 0), scale=1.0):
    before = set(bpy.data.objects); fn(*args); new = [o for o in bpy.data.objects if o not in before]
    Mx = Matrix.Translation((wx, wy, 0)) @ Matrix.Rotation(math.radians(rot), 4, 'Z') @ Matrix.Scale(scale, 4) @ Matrix.Translation((-pivot[0], pivot[1], 0))
    for o in new: o.matrix_basis = Mx @ o.matrix_basis
    return new

def plane(name, x0, y0, x1, y1, z, mat):
    me = bpy.data.meshes.new(name); me.from_pydata([(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [], [(0, 1, 2, 3)])
    me.materials.append(mat); o = bpy.data.objects.new(name, me); bpy.context.collection.objects.link(o); return o

def wet_ground():
    m, nt = lib._nodes(); m.name = 'wetground'
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.6; nz.inputs['Detail'].default_value = 6
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].position = 0.42; r.color_ramp.elements[1].position = 0.56
    r.color_ramp.elements[0].color = (0.35, 0.35, 0.35, 1); r.color_ramp.elements[1].color = (0.9, 0.9, 0.9, 1)   # puddles (dark/smooth) vs damp concrete
    nt.links.new(nz.outputs['Fac'], r.inputs['Fac'])
    nt.links.new(r.outputs[0], bs.inputs['Roughness'])
    bs.inputs['Base Color'].default_value = srgb('#1d2128'); bs.inputs['Metallic'].default_value = 0.2; bs.inputs['Specular IOR Level'].default_value = 1.0
    return m

def oily_sea():
    m, nt = lib._nodes(); m.name = 'sea'
    out = nt.nodes.new('ShaderNodeOutputMaterial'); bs = nt.nodes.new('ShaderNodeBsdfPrincipled'); nt.links.new(bs.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (0.9, 2.6, 1)
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 1.5; nz.inputs['Detail'].default_value = 4
    nt.links.new(mp.outputs[0], nz.inputs['Vector'])
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 0.2; bm.inputs['Distance'].default_value = 0.2
    nt.links.new(nz.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs[0], bs.inputs['Normal'])
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 0.35; n2.inputs['Detail'].default_value = 3
    nt.links.new(tc.outputs['Object'], n2.inputs['Vector'])
    r = nt.nodes.new('ShaderNodeValToRGB'); r.color_ramp.elements[0].color = srgb('#0b1c22'); r.color_ramp.elements[1].color = srgb('#2a1438')   # teal <-> violet oil sheen
    e = r.color_ramp.elements.new(0.5); e.color = srgb('#10302c')
    nt.links.new(n2.outputs['Fac'], r.inputs['Fac']); nt.links.new(r.outputs[0], bs.inputs['Base Color'])
    bs.inputs['Roughness'].default_value = 0.16; bs.inputs['Metallic'].default_value = 0.6
    return m

if __name__ == '__main__':
    a = args(); W, H, spp = (int(a[0]), int(a[1]), int(a[2])) if len(a) >= 3 else (480, 270, 24)
    lib.reset(); setup_render(spp, W, H)
    sc = bpy.context.scene; sc.render.film_transparent = False
    sc.view_settings.exposure = 0.2
    for o in bpy.data.objects:
        if o.type == 'LIGHT': o.data.energy *= {'moon': 0.22, 'sodium': 0.12, 'rimc': 0.5, 'rimm': 0.4}.get(o.name, 1)
    sc.world.node_tree.nodes['Background'].inputs['Strength'].default_value = 0.35
    sc.cycles.max_bounces = 6; sc.cycles.glossy_bounces = 4; sc.cycles.sample_clamp_indirect = 3.0
    plane('sea', -150, -40, 150, 160, -0.02, oily_sea())
    plane('land', 1.2, 0.2, 14.0, 9.0, 0.0, wet_ground())
    # layout (world X right-ish, Y away). Left third (x<2) kept sparse.
    place(MD.house, (0,), 2.4, 1.6, pivot=(0.5, 0.5), rot=0) if False else None
    for (x, y, v, rz) in ((2.4, 2.2, 0, 0), (3.6, 2.8, 1, 0), (5.2, 3.8, 0, 0), (6.5, 3.2, 2, 0)):
        place(MD.house, (v,), x, y, rz)
    place(MD.smelter, (), 9.0, 1.6)
    place(MD.wind_turbine, (), 8.2, 6.0)
    place(MD.port, (), 7.0, 0.4, rot=-90, pivot=(1.0, 1.0))
    place(MD.signal_relay, (), 4.2, 0.6, scale=1.4)
    place(MD.coastal_battery, (), 9.6, 0.2, rot=0, scale=0.7) if False else None
    # moored hauler broadside to the quay (port rot -90: quay faces -Y at y ~ 0.4 - 1 => water at y < ~ -0.6)
    place(MD.hauler_model, (), 7.0, -0.95, rot=0)
    # distant patrol with a sweeping searchlight on the horizon
    place(MD.patrol_model, (), 4.0, 38.0, rot=200, scale=4.5)
    ld = bpy.data.lights.new('sweep', 'SPOT'); ld.energy = 90000; ld.spot_size = math.radians(14); ld.spot_blend = 0.5; ld.color = (0.85, 0.95, 1.0); ld.shadow_soft_size = 0.3
    lo = bpy.data.objects.new('sweep', ld); bpy.context.collection.objects.link(lo); lo.location = (4.0, 38.0, 1.0)
    lo.rotation_euler = (Vector((-0.55, -1.0, -0.06))).to_track_quat('-Z', 'Y').to_euler()
    # cinematic lights: cool backlight from the horizon, magenta/amber kicks
    pl = lambda p, c, w, r=0.5: point_light(p, c, w, r)
    pl((5.0, -2.0, 2.2), (1.0, 0.45, 0.2), 90, 0.4); pl((2.0, -1.5, 1.5), (0.2, 0.8, 1.0), 40, 0.4)
    # camera
    cam = bpy.data.cameras.new('cam'); cam.lens = 24; cam.clip_end = 400; cam.dof.use_dof = True
    co = bpy.data.objects.new('cam', cam); bpy.context.collection.objects.link(co); sc.camera = co
    co.location = (10.4, -5.0, 1.2)
    tgt = Vector((4.8, 2.4, 1.0)); co.rotation_euler = (tgt - co.location).to_track_quat('-Z', 'Y').to_euler()
    cam.dof.focus_distance = (tgt - co.location).length; cam.dof.aperture_fstop = 7.0
    sc.render.resolution_x = W; sc.render.resolution_y = H
    sc.render.filepath = os.path.join(WORK, 'title_raw.png'); bpy.ops.render.render(write_still=True); print('TITLE', W, H, spp, flush=True)
