"""冒烟测试：直接调用 Predictor，验证高分/低分样本与 SHAP 贡献度合理性。"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from app.predictor import Predictor  # noqa: E402
from app import schema  # noqa: E402


def make_answers(value_fn):
    a = {"gender": "男", "marital": "已婚/同居", "police_type": "刑警"}
    for sec in schema.SECTIONS:
        for dim in sec.dimensions:
            for j in range(dim.n_items):
                a[f"{sec.id}.{dim.key}.{j}"] = value_fn(sec.scale)
    return a


p = Predictor()
print("model_info:", json.dumps(p.model_info(), ensure_ascii=False))

for label, fn in [
    ("LOW (all min)", lambda s: 1),
    ("MID (all middle)", lambda s: (s + 1) // 2),
    ("HIGH (all max)", lambda s: s),
]:
    r = p.predict(make_answers(fn))
    contrib_sum = sum(c["value"] for c in r["contributions"])
    print(f"\n=== {label} ===")
    print(f"  score={r['score']} level={r['level']}({r['levelLabel']}) pct={r['percentile']}")
    print(f"  contrib_sum={contrib_sum:.3f}  top3={[ (c['name'],c['value']) for c in r['contributions'][:3] ]}")
    print(f"  advice[0]={r['advice'][0][:40]}...")

print("\nOK")
