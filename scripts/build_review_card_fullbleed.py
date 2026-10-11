from pathlib import Path
import numpy as np
import trimesh
from PIL import Image
from trimesh.visual.material import PBRMaterial

ROOT = Path(__file__).resolve().parents[1]
MODEL = ROOT / "src/nfc-review-card-3d.glb"
FRONT_SOURCE = ROOT / "src/media/v9/01-review-card-design-render.webp"

# Preserve the previous model's back texture so only the front artwork changes.
old_scene = trimesh.load(MODEL, force="scene")
back_texture = None
for name, geom in old_scene.geometry.items():
    if name.lower() == "back":
        material = getattr(geom.visual, "material", None)
        image = getattr(material, "baseColorTexture", None)
        if image is not None:
            back_texture = image.convert("RGB")
            break
if back_texture is None:
    raise RuntimeError("Back texture not found in previous GLB")

# Crop the clean render to the physical card itself, removing the white studio margin.
source = Image.open(FRONT_SOURCE).convert("RGB")
w, h = source.size
crop = (
    round(w * 0.0765),
    round(h * 0.0805),
    round(w * 0.9240),
    round(h * 0.9115),
)
front_texture = source.crop(crop).resize((512, 512), Image.Resampling.LANCZOS)

def rounded_rect(width=0.1, height=0.1, radius=0.006, segments=16):
    points = []
    centers = [
        (width/2-radius, height/2-radius),
        (-width/2+radius, height/2-radius),
        (-width/2+radius, -height/2+radius),
        (width/2-radius, -height/2+radius),
    ]
    ranges = [(0,90),(90,180),(180,270),(270,360)]
    for (cx, cy), (a0, a1) in zip(centers, ranges):
        for a in np.linspace(a0, a1, segments, endpoint=False):
            r = np.deg2rad(a)
            points.append([cx + radius*np.cos(r), cy + radius*np.sin(r)])
    return np.asarray(points, dtype=float)

def face(perimeter, z, front, texture):
    count = len(perimeter)
    vertices = np.vstack([
        [0,0,z],
        np.column_stack([perimeter, np.full(count,z)])
    ])
    faces = []
    for i in range(count):
        j = (i+1) % count
        faces.append([0,1+i,1+j] if front else [0,1+j,1+i])

    uv = np.zeros((len(vertices),2), dtype=float)
    uv[0] = [0.5,0.5]
    # Full-bleed mapping: artwork spans the complete 100 x 100 mm front face.
    uv[1:,0] = (perimeter[:,0] + 0.05) / 0.10
    uv[1:,1] = (perimeter[:,1] + 0.05) / 0.10

    material = PBRMaterial(
        baseColorTexture=texture,
        metallicFactor=0.0,
        roughnessFactor=0.78,
    )
    return trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces),
        visual=trimesh.visual.TextureVisuals(uv=uv, material=material),
        process=False,
    )

def edge(perimeter, half_thickness=0.00125):
    count = len(perimeter)
    vertices = []
    faces = []
    for x,y in perimeter:
        vertices.append([x,y,half_thickness])
        vertices.append([x,y,-half_thickness])
    for i in range(count):
        j=(i+1)%count
        a,b=2*i,2*i+1
        c,d=2*j,2*j+1
        faces.extend([[a,b,d],[a,d,c]])

    material=PBRMaterial(
        baseColorFactor=[0.96,0.97,0.98,1.0],
        metallicFactor=0.0,
        roughnessFactor=0.62,
    )
    return trimesh.Trimesh(
        vertices=np.asarray(vertices),
        faces=np.asarray(faces),
        visual=trimesh.visual.TextureVisuals(material=material),
        process=False,
    )

perimeter=rounded_rect()
half=0.00125  # subtle 2.5 mm visual thickness

scene=trimesh.Scene()
scene.add_geometry(face(perimeter, half+0.00001, True, front_texture), node_name="Front", geom_name="Front")
scene.add_geometry(face(perimeter, -half-0.00001, False, back_texture), node_name="Back", geom_name="Back")
scene.add_geometry(edge(perimeter, half), node_name="Edge", geom_name="Edge")

# Raised adhesive strips on the rear side.
# 2 mm real extrusion with a visible darker side wall and chamfer so the
# thickness remains readable even when the rear face is viewed almost head-on.
adhesive_top_material = PBRMaterial(
    baseColorFactor=[0.015, 0.62, 1.0, 1.0],
    metallicFactor=0.0,
    roughnessFactor=0.34,
)
adhesive_bevel_material = PBRMaterial(
    baseColorFactor=[0.01, 0.46, 0.88, 1.0],
    metallicFactor=0.0,
    roughnessFactor=0.38,
)
adhesive_side_material = PBRMaterial(
    baseColorFactor=[0.005, 0.30, 0.68, 1.0],
    metallicFactor=0.0,
    roughnessFactor=0.44,
)

def material_face(perimeter, z, negative_z, material):
    count = len(perimeter)
    vertices = np.vstack([
        [0, 0, z],
        np.column_stack([perimeter, np.full(count, z)])
    ])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.append([0, 1+j, 1+i] if negative_z else [0, 1+i, 1+j])
    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces),
        visual=trimesh.visual.TextureVisuals(material=material),
        process=False,
    )
    _ = mesh.vertex_normals
    return mesh

def ring_surface(a, za, b, zb, material):
    count = len(a)
    vertices = np.vstack([
        np.column_stack([a, np.full(count, za)]),
        np.column_stack([b, np.full(count, zb)]),
    ])
    faces = []
    for i in range(count):
        j = (i + 1) % count
        faces.extend([
            [i, count+i, count+j],
            [i, count+j, j],
        ])
    mesh = trimesh.Trimesh(
        vertices=vertices,
        faces=np.asarray(faces),
        visual=trimesh.visual.TextureVisuals(material=material),
        process=False,
    )
    _ = mesh.vertex_normals
    return mesh

strip_width = 0.0155
strip_height = 0.078
strip_thickness = 0.00200
strip_radius = 0.0019
bevel = 0.00032
base_z = -half - 0.00004
top_z = base_z - strip_thickness
shoulder_z = top_z + bevel

strip_outer = rounded_rect(
    width=strip_width,
    height=strip_height,
    radius=strip_radius,
    segments=10,
)
strip_top = rounded_rect(
    width=strip_width - 0.00075,
    height=strip_height - 0.00075,
    radius=max(0.0008, strip_radius - 0.00038),
    segments=10,
)

for idx, x in enumerate((-0.0335, 0.0335), start=1):
    outer = strip_outer.copy()
    top = strip_top.copy()
    outer[:, 0] += x
    top[:, 0] += x

    side = ring_surface(
        outer, base_z,
        outer, shoulder_z,
        adhesive_side_material
    )
    chamfer = ring_surface(
        outer, shoulder_z,
        top, top_z,
        adhesive_bevel_material
    )
    cap = material_face(
        top, top_z,
        True,
        adhesive_top_material
    )

    scene.add_geometry(
        side,
        node_name=f"RearAdhesiveStrip{idx}Side",
        geom_name=f"RearAdhesiveStrip{idx}Side"
    )
    scene.add_geometry(
        chamfer,
        node_name=f"RearAdhesiveStrip{idx}Bevel",
        geom_name=f"RearAdhesiveStrip{idx}Bevel"
    )
    scene.add_geometry(
        cap,
        node_name=f"RearAdhesiveStrip{idx}Top",
        geom_name=f"RearAdhesiveStrip{idx}Top"
    )

MODEL.write_bytes(scene.export(file_type="glb"))
print(f"Rebuilt full-bleed review card model: {MODEL.stat().st_size} bytes")
