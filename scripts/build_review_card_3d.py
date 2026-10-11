from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageEnhance, ImageFilter
from trimesh.visual.material import PBRMaterial

ROOT = Path(__file__).resolve().parents[1]
FRONT_SOURCE = ROOT / "src/media/v9/01-review-card-design-render.webp"
OUTPUT = ROOT / "src/nfc-review-card-3d.glb"

TEXTURE_SIZE = 768
VISIBLE_THICKNESS = 0.0040
FACE_Z = VISIBLE_THICKNESS / 2
SIDE_Z = 0.00155

def rounded_rect(w=0.1, h=0.1, r=0.007, segments=32):
    points = []
    centers = [
        (w/2-r, h/2-r),
        (-w/2+r, h/2-r),
        (-w/2+r, -h/2+r),
        (w/2-r, -h/2+r),
    ]
    ranges = [(0,90),(90,180),(180,270),(270,360)]
    for (cx, cy), (a0, a1) in zip(centers, ranges):
        for angle in np.linspace(a0, a1, segments, endpoint=False):
            rad = np.deg2rad(angle)
            points.append([cx + r*np.cos(rad), cy + r*np.sin(rad)])
    return np.asarray(points, dtype=float)

def prepare_front():
    image = Image.open(FRONT_SOURCE).convert("RGB")
    image = image.resize((TEXTURE_SIZE, TEXTURE_SIZE), Image.Resampling.LANCZOS)
    image = ImageEnhance.Color(image).enhance(1.10)
    image = ImageEnhance.Contrast(image).enhance(1.06)
    image = ImageEnhance.Sharpness(image).enhance(1.18)
    return image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=80, threshold=3))

def make_face(perimeter, z, front=True, texture=None, material=None):
    count = len(perimeter)
    vertices = np.vstack([[0,0,z], np.column_stack([perimeter, np.full(count,z)])])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.append([0,1+i,1+j] if front else [0,1+j,1+i])

    if texture is not None:
        uv = np.zeros((len(vertices),2), dtype=float)
        uv[0] = [0.5,0.5]
        uv[1:,0] = (perimeter[:,0] + 0.05) / 0.1
        uv[1:,1] = (perimeter[:,1] + 0.05) / 0.1
        material = PBRMaterial(
            baseColorTexture=texture,
            metallicFactor=0.0,
            roughnessFactor=0.60,
        )
        visual = trimesh.visual.TextureVisuals(uv=uv, material=material)
    else:
        visual = trimesh.visual.TextureVisuals(material=material)

    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces),
        visual=visual,
        process=False,
    )
    _ = mesh.vertex_normals
    return mesh

def ring_strip(a, za, b, zb, material):
    count = len(a)
    vertices = np.vstack([
        np.column_stack([a, np.full(count,za)]),
        np.column_stack([b, np.full(count,zb)]),
    ])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.extend([[i,j,count+j],[i,count+j,count+i]])
    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces),
        visual=trimesh.visual.TextureVisuals(material=material),
        process=False,
    )
    _ = mesh.vertex_normals
    return mesh

front_texture = prepare_front()
inner = rounded_rect(0.0994,0.0994,0.0067,32)
outer = rounded_rect(0.1000,0.1000,0.0070,32)

plastic = PBRMaterial(
    baseColorFactor=[0.94,0.96,0.98,1.0],
    metallicFactor=0.0,
    roughnessFactor=0.38,
)
back_material = PBRMaterial(
    baseColorFactor=[0.975,0.985,0.995,1.0],
    metallicFactor=0.0,
    roughnessFactor=0.52,
)
blue_foam = PBRMaterial(
    baseColorFactor=[0.0,0.52,0.94,1.0],
    metallicFactor=0.0,
    roughnessFactor=0.46,
)
center_pad = PBRMaterial(
    baseColorFactor=[0.90,0.94,0.98,0.72],
    metallicFactor=0.0,
    roughnessFactor=0.54,
    alphaMode="BLEND",
)

scene = trimesh.Scene()
scene.add_geometry(make_face(inner, FACE_Z, True, texture=front_texture), node_name="FrontPrint", geom_name="FrontPrint")
scene.add_geometry(make_face(inner, -FACE_Z, False, material=back_material), node_name="Back", geom_name="Back")
scene.add_geometry(ring_strip(inner, FACE_Z, outer, SIDE_Z, plastic), node_name="FrontBevel", geom_name="FrontBevel")
scene.add_geometry(ring_strip(outer, SIDE_Z, outer, -SIDE_Z, plastic), node_name="Edge", geom_name="Edge")
scene.add_geometry(ring_strip(outer, -SIDE_Z, inner, -FACE_Z, plastic), node_name="BackBevel", geom_name="BackBevel")

# Raised adhesive strips copied from the real rear-side layout.
strip_w, strip_h, strip_t = 0.017, 0.079, 0.00085
for index, x in enumerate((-0.0335, 0.0335), start=1):
    strip = trimesh.creation.box(extents=[strip_w, strip_h, strip_t])
    strip.apply_translation([x, 0, -FACE_Z - strip_t/2 - 0.00004])
    strip.visual = trimesh.visual.TextureVisuals(material=blue_foam)
    _ = strip.vertex_normals
    scene.add_geometry(strip, node_name=f"AdhesiveStrip{index}", geom_name=f"AdhesiveStrip{index}")

pad = trimesh.creation.cylinder(radius=0.0115, height=0.00055, sections=64)
pad.apply_translation([0,0,-FACE_Z-0.00055/2-0.00005])
pad.visual = trimesh.visual.TextureVisuals(material=center_pad)
_ = pad.vertex_normals
scene.add_geometry(pad, node_name="CenterPad", geom_name="CenterPad")

OUTPUT.write_bytes(scene.export(file_type="glb"))
print(f"Generated {OUTPUT} ({OUTPUT.stat().st_size} bytes)")
