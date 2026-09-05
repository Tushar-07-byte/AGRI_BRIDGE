import os
import json

for name, path in [
    ("Phase1", r"c:\Users\TUSHAR\Projects\AgriBridge - 2\backend\AI_Engine\AgriBridge_Wheat_EfficientNetB0_Phase1.keras"),
    ("Stage2", r"c:\Users\TUSHAR\Projects\AgriBridge - 2\AgriBridge_Wheat_EfficientNetB0_Stage2_Best.keras")
]:
    with open(os.path.join(path, "config.json"), "r") as f:
        cfg = json.load(f)
    print(f"\n=== {name} Nested efficientnetb0 ===")
    layers = cfg.get("config", {}).get("layers", [])
    for l in layers:
        if l.get("name") == "efficientnetb0":
            nested = l.get("config", {}).get("layers", [])
            print(f"Total nested layers in efficientnetb0: {len(nested)}")
            for i, nl in enumerate(nested[:8]):
                cname = nl.get("class_name")
                name_ = nl.get("name")
                cfg_ = nl.get("config", {})
                print(f"  {i}: {cname} ({name_})")
                if cname in ["Rescaling", "Normalization"]:
                    print(f"      scale/mean/var: {cfg_}")

