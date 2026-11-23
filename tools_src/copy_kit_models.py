"""Copy the kit models the hub uses (gltf + bin + referenced textures) from tools/vendor into art/.

Usage: python tools_src/copy_kit_models.py
"""

import json
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
VENDOR_DIR = PROJECT_DIR / "tools" / "vendor"

MODELS = {
    VENDOR_DIR / "nature" / "glTF": (
        PROJECT_DIR / "art" / "nature",
        [
            "CommonTree_1", "CommonTree_2", "CommonTree_3", "CommonTree_4", "CommonTree_5",
            "Pine_1", "Pine_2", "Pine_3", "Bush_Common", "Bush_Common_Flowers",
            "Flower_3_Group", "Flower_4_Group", "Grass_Common_Short", "Grass_Wispy_Short", "Rock_Medium_1",
        ],
    ),
    VENDOR_DIR / "props" / "Exports" / "glTF": (
        PROJECT_DIR / "art" / "props",
        [
            "Stall_Empty", "Stall_Cart_Empty", "Barrel", "Barrel_Apples", "Crate_Wooden",
            "FarmCrate_Apple", "FarmCrate_Carrot", "Bucket_Wooden_1", "Banner_1", "Banner_2", "Table_Large", "Stool",
        ],
    ),
}


def copy_model(source_dir: Path, target_dir: Path, model_name: str) -> None:
    gltf_path = source_dir / f"{model_name}.gltf"
    document = json.loads(gltf_path.read_text(encoding="utf-8"))
    referenced_files = [buffer["uri"] for buffer in document["buffers"]] + [image["uri"] for image in document.get("images", [])]

    shutil.copy2(gltf_path, target_dir / gltf_path.name)

    for file_name in referenced_files:
        shutil.copy2(source_dir / file_name, target_dir / file_name)


if __name__ == "__main__":
    for source_dir, (target_dir, model_names) in MODELS.items():
        target_dir.mkdir(parents=True, exist_ok=True)

        for model_name in model_names:
            copy_model(source_dir, target_dir, model_name)

        print(f"COPIED {len(model_names)} models -> {target_dir}")
