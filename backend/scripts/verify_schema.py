"""校验 schema 的列索引与题目数量是否与原始数据一致。"""
import sys
import os
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from app import schema  # noqa: E402

PATH = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/WenshuSpace/软著数据.xlsx"
df = pd.read_excel(PATH)
cols = list(df.columns)

ok = True
for sec in schema.SECTIONS:
    for dim in sec.dimensions:
        assert len(dim.columns) == dim.n_items, f"{dim.key} n_items mismatch"
        for c in dim.columns:
            name = cols[c]
            # 验证该列是该量表分值范围内的整数题目
            vals = df[name].dropna().unique()
            mn, mx = int(min(vals)), int(max(vals))
            flag = "OK" if mx <= sec.scale else "!!"
            if mx > sec.scale:
                ok = False
            print(f"[{flag}] {sec.id:9} {dim.key:15} col{c:>3} range[{mn},{mx}] :: {name[:30]}")

print("\nDemographics:")
for key, c in schema.DEMO_COLUMNS.items():
    print(f"  {key:12} col{c} -> {cols[c]!r} :: {df[cols[c]].dropna().unique()[:6]}")

print(f"\nTarget mean col{schema.TARGET_MEAN_COL} -> {cols[schema.TARGET_MEAN_COL]!r}")
print(f"Target class col{schema.TARGET_CLASS_COL} -> {cols[schema.TARGET_CLASS_COL]!r}")
print(f"\nN_LIKERT={schema.N_LIKERT}  N_FEATURES={schema.N_FEATURES}")
print("ALL OK" if ok else "SCHEMA MISMATCH")
