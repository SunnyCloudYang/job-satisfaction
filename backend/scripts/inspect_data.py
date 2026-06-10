"""一次性数据探查脚本：打印列名、范围、目标分布，辅助特征工程。"""
import sys
import pandas as pd

PATH = sys.argv[1] if len(sys.argv) > 1 else "/Volumes/WenshuSpace/软著数据.xlsx"
df = pd.read_excel(PATH)

print("shape:", df.shape)
print("\n=== columns (index | name | dtype | nunique | sample) ===")
for i, c in enumerate(df.columns):
    s = df[c]
    sample = s.dropna().unique()[:4]
    print(f"{i:>3} | {c!r} | {s.dtype} | nunique={s.nunique()} | {sample}")

print("\n=== columns containing 满意 ===")
for c in df.columns:
    if "满意" in str(c):
        print(repr(c), "->", df[c].dropna().unique()[:6])
