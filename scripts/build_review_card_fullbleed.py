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

# Two independent rear adhesive strips: one on the left and one on the right.
# Each strip protrudes exactly 1 mm from the rear surface.
adhesive_material = PBRMaterial(
    baseColorFactor=[0.02, 0.60, 0.98, 1.0],
    metallicFactor=0.0,
    roughnessFactor=0.38,
)

strip_width = 0.0212
strip_height = 0.0940
strip_thickness = 0.00100  # 1 mm
rear_surface_z = -half - 0.00004

for idx, x in enumerate((-0.0335, 0.0335), start=1):
    strip = trimesh.creation.box(
        extents=[strip_width, strip_height, strip_thickness]
    )
    strip.apply_translation([
        x,
        0.0,
        rear_surface_z - strip_thickness / 2
    ])
    strip.visual = trimesh.visual.TextureVisuals(material=adhesive_material)
    _ = strip.vertex_normals
    scene.add_geometry(
        strip,
        node_name=f"RearAdhesiveStrip{idx}",
        geom_name=f"RearAdhesiveStrip{idx}"
    )

MODEL.write_bytes(scene.export(file_type="glb"))
print(f"Rebuilt full-bleed review card model: {MODEL.stat().st_size} bytes")
