"""全面评估工作满意度预测模型的效果。

用 5 折交叉验证的 out-of-fold 预测（避免乐观偏差），输出：
- 回归指标：MAE / RMSE / R² / 中位绝对误差，以及与"只猜均值"基线的对比
- 分类指标：低/中/高三档的准确率、混淆矩阵、各档精确率/召回率
- 误差结构：按真实分数分箱的 MAE，预测值落在 ±0.25/±0.5 内的比例
- 重要性：按维度聚合的特征重要性 top 排序

用法:
    python backend/scripts/evaluate.py [path/to/data.xlsx]
"""
from __future__ import annotations

import os
import sys
from collections import defaultdict

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import KFold

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from app import schema  # noqa: E402
from scripts.train import DEFAULT_DATA, build_matrix, make_weights  # noqa: E402

PARAMS = dict(
    n_estimators=400,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.85,
    colsample_bytree=0.85,
    reg_lambda=1.5,
    reg_alpha=0.1,
    min_child_weight=3,
    objective="reg:squarederror",
    random_state=42,
    n_jobs=-1,
)

# 从 metadata 读取阈值，与线上模型保持一致
_META = os.path.join(BACKEND, "models", "metadata.json")
try:
    import json
    with open(_META, encoding="utf-8") as _f:
        _ct = json.load(_f)["class_thresholds"]
    CUT_LOW_MID = _ct["low_mid"]
    CUT_MID_HIGH = _ct["mid_high"]
except Exception:
    CUT_LOW_MID = 2.975
    CUT_MID_HIGH = 3.975


def to_class(v: np.ndarray) -> np.ndarray:
    out = np.full(v.shape, "中", dtype=object)
    out[v < CUT_LOW_MID] = "低"
    out[v >= CUT_MID_HIGH] = "高"
    return out


def main() -> None:
    data_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    print(f"Loading {data_path} ...")
    df = pd.read_excel(data_path)
    X, y, cls_true_raw = build_matrix(df)
    n = len(y)
    print(f"  samples={n}  features={X.shape[1]}")
    print(f"  target: mean={y.mean():.3f}  std={y.std():.3f}  min={y.min():.2f}  max={y.max():.2f}")

    # ---- out-of-fold 预测（带样本权重，与训练一致）----
    w = make_weights(y)
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    yp = np.zeros_like(y, dtype=float)
    for tr, te in kf.split(X):
        m = xgb.XGBRegressor(**PARAMS).fit(X[tr], y[tr], sample_weight=w[tr])
        yp[te] = m.predict(X[te])
    yp = np.clip(yp, 1.0, 5.0)

    # ---- 回归指标 ----
    mae = mean_absolute_error(y, yp)
    rmse = float(np.sqrt(mean_squared_error(y, yp)))
    r2 = r2_score(y, yp)
    medae = float(np.median(np.abs(y - yp)))

    # 基线：永远预测样本均值
    base_pred = np.full_like(y, y.mean())
    base_mae = mean_absolute_error(y, base_pred)
    base_rmse = float(np.sqrt(mean_squared_error(y, base_pred)))

    print("\n================ 回归效果（5 折 out-of-fold）================")
    print(f"  MAE         {mae:.4f}      (基线-猜均值 {base_mae:.4f}，降低 {(1-mae/base_mae)*100:.1f}%)")
    print(f"  RMSE        {rmse:.4f}      (基线 {base_rmse:.4f}，降低 {(1-rmse/base_rmse)*100:.1f}%)")
    print(f"  R²          {r2:.4f}")
    print(f"  中位绝对误差 {medae:.4f}")
    within025 = float(np.mean(np.abs(y - yp) <= 0.25)) * 100
    within050 = float(np.mean(np.abs(y - yp) <= 0.50)) * 100
    print(f"  |误差|≤0.25  {within025:.1f}%")
    print(f"  |误差|≤0.50  {within050:.1f}%")

    # ---- 分类指标（低/中/高）----
    cls_true = to_class(y)
    cls_pred = to_class(yp)
    labels = ["低", "中", "高"]
    acc = accuracy_score(cls_true, cls_pred)
    cm = confusion_matrix(cls_true, cls_pred, labels=labels)

    print("\n================ 三档分类效果（低/中/高）================")
    print(f"  准确率 Accuracy: {acc*100:.1f}%")
    print("\n  混淆矩阵（行=真实, 列=预测）:")
    header = "          " + "".join(f"{l:>8}" for l in labels)
    print(header)
    for i, l in enumerate(labels):
        row = f"  真实 {l}  " + "".join(f"{cm[i][j]:>8}" for j in range(len(labels)))
        print(row)

    print("\n  各档精确率 / 召回率:")
    for i, l in enumerate(labels):
        tp = cm[i][i]
        col_sum = cm[:, i].sum()
        row_sum = cm[i, :].sum()
        prec = tp / col_sum if col_sum else 0
        rec = tp / row_sum if row_sum else 0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0
        print(f"    {l}: 精确率 {prec*100:5.1f}%   召回率 {rec*100:5.1f}%   F1 {f1*100:5.1f}%   (样本 {row_sum})")

    # 相邻档误判 vs 跨档误判（低<->高 才是严重错误）
    severe = cm[0][2] + cm[2][0]
    print(f"\n  严重误判（低<->高 完全反向）: {severe} 条 ({severe/n*100:.2f}%)")

    # ---- 误差按真实分数分箱 ----
    print("\n================ 误差随真实分数的分布 ================")
    bins = [1, 2, 2.5, 3, 3.5, 4, 4.5, 5.01]
    err = np.abs(y - yp)
    bias = yp - y
    print(f"  {'分数区间':<12}{'样本':>6}{'MAE':>8}{'平均偏差':>10}")
    for k in range(len(bins) - 1):
        m = (y >= bins[k]) & (y < bins[k + 1])
        if m.sum() == 0:
            continue
        print(f"  [{bins[k]:.1f}, {bins[k+1]:.1f})   {m.sum():>6}{err[m].mean():>8.3f}{bias[m].mean():>+10.3f}")
    print("  注: 平均偏差为正=高估, 为负=低估")

    # ---- 维度重要性 ----
    print("\n================ 维度重要性（gain 聚合）================")
    model = xgb.XGBRegressor(**PARAMS).fit(X, y)
    booster = model.get_booster()
    score = booster.get_score(importance_type="gain")  # {'f0':gain,...}
    feat_names = schema.feature_names()
    dim_gain: dict[str, float] = defaultdict(float)
    demo_gain = 0.0
    for fkey, g in score.items():
        idx = int(fkey[1:])
        name = feat_names[idx]
        if name.startswith("demo."):
            demo_gain += g
            continue
        # name like "justice.distributive.0" -> dim key "distributive"
        dim = name.split(".")[1]
        dim_gain[dim] += g
    total = sum(dim_gain.values()) + demo_gain
    ranked = sorted(dim_gain.items(), key=lambda x: -x[1])
    dim_names = schema.DIMENSION_NAMES
    for dim, g in ranked:
        print(f"    {dim_names.get(dim, dim):<14} {g/total*100:5.1f}%")
    print(f"    {'人口学变量':<14} {demo_gain/total*100:5.1f}%")

    print("\nDone.")


if __name__ == "__main__":
    main()
