"""训练 XGBoost 回归模型，预测工作满意度均分。

用法:
    python backend/scripts/train.py [path/to/data.xlsx]

产物（写入 backend/models/）:
    model.json        XGBoost 模型
    metadata.json     特征顺序、评估指标、样本统计、维度基准、分类阈值
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import KFold, train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from app import schema  # noqa: E402

MODELS_DIR = os.path.join(BACKEND, "models")
DEFAULT_DATA = "/Volumes/WenshuSpace/软著数据.xlsx"

# 样本加权（缓解向均值回归 + 抬升稀少的高分样本）。
# 经 5 折 OOF 对比，(strength=0.8, high_boost=1.4) 在精度损失最小的前提下
# 明显改善两端偏差与高档召回。
WEIGHT_STRENGTH = 0.8
WEIGHT_HIGH_BOOST = 1.4
HIGH_CUTOFF = 3.975  # 高分样本判定线（仅用于加权）
MIN_ACC = 0.65       # 阈值搜索时的整体准确率下限


def make_weights(y: np.ndarray) -> np.ndarray:
    """离均值越远权重越大；高分样本额外加权。"""
    w = 1.0 + WEIGHT_STRENGTH * np.abs(y - y.mean()) / y.std()
    w[y >= HIGH_CUTOFF] *= WEIGHT_HIGH_BOOST
    return w


def _to_class(v: np.ndarray, lo: float, hi: float) -> np.ndarray:
    out = np.full(v.shape, "中", dtype=object)
    out[v < lo] = "低"
    out[v >= hi] = "高"
    return out


def tune_thresholds(y: np.ndarray, yp: np.ndarray) -> tuple[float, float]:
    """基于 OOF 预测搜索阈值：在整体 acc>=MIN_ACC 的前提下最大化三档 macro 召回。

    若没有任何阈值满足 acc 下限，则回退到 acc 最高的阈值。
    """
    ct = _to_class(y, 2.975, 3.975)
    best = None        # 满足 acc 下限中 macro 最优
    fallback = None    # 全局 acc 最优
    for lo in np.arange(2.70, 3.16, 0.025):
        for hi in np.arange(3.55, 4.16, 0.025):
            if hi <= lo + 0.2:
                continue
            cp = _to_class(yp, lo, hi)
            recs = [float((cp[ct == l] == l).mean()) for l in ["低", "中", "高"]]
            macro = float(np.mean(recs))
            acc = float((ct == cp).mean())
            if fallback is None or acc > fallback[0]:
                fallback = (acc, lo, hi)
            if acc >= MIN_ACC and (best is None or macro > best[0]):
                best = (macro, lo, hi)
    chosen = best if best is not None else fallback
    return round(float(chosen[1]), 3), round(float(chosen[2]), 3)


def oof_predict(params: dict, X: np.ndarray, y: np.ndarray, w: np.ndarray) -> np.ndarray:
    """带样本权重的 5 折 out-of-fold 预测。"""
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    pred = np.zeros_like(y, dtype=float)
    for tr, te in kf.split(X):
        m = xgb.XGBRegressor(**params).fit(X[tr], y[tr], sample_weight=w[tr])
        pred[te] = m.predict(X[te])
    return np.clip(pred, 1.0, 5.0)


def build_matrix(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """从原始 DataFrame 构造特征矩阵 X、回归目标 y、分类标签 cls。"""
    cols = list(df.columns)
    rows = []
    for _, r in df.iterrows():
        answers: dict = {}
        # demographics
        for key, ci in schema.DEMO_COLUMNS.items():
            answers[key] = r[cols[ci]]
        # likert
        for sec in schema.SECTIONS:
            for dim in sec.dimensions:
                for j, ci in enumerate(dim.columns):
                    answers[f"{sec.id}.{dim.key}.{j}"] = r[cols[ci]]
        rows.append(schema.answers_to_vector(answers))

    X = np.asarray(rows, dtype=float)
    y = df[cols[schema.TARGET_MEAN_COL]].to_numpy(dtype=float)
    cls = df[cols[schema.TARGET_CLASS_COL]].astype(str).to_numpy()
    return X, y, cls


def main() -> None:
    data_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    print(f"Loading {data_path} ...")
    df = pd.read_excel(data_path)
    print(f"  rows={len(df)}")

    X, y, cls = build_matrix(df)
    feat_names = schema.feature_names()
    assert X.shape[1] == len(feat_names), "feature count mismatch"
    print(f"  X={X.shape}  y range=[{y.min():.2f},{y.max():.2f}]")

    params = dict(
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

    # 样本权重（缓解向均值回归）
    w = make_weights(y)
    print(f"  sample weights: min={w.min():.2f} max={w.max():.2f} mean={w.mean():.2f}")

    # 5 折 out-of-fold（带权）评估泛化能力
    cv_pred = oof_predict(params, X, y, w)
    cv_mae = mean_absolute_error(y, cv_pred)
    cv_r2 = r2_score(y, cv_pred)
    print(f"\n5-fold OOF (weighted):  MAE={cv_mae:.4f}  R2={cv_r2:.4f}")

    # 基于 OOF 预测搜索更均衡的三档阈值
    cut_low_mid, cut_mid_high = tune_thresholds(y, cv_pred)
    cp = _to_class(cv_pred, cut_low_mid, cut_mid_high)
    ct = _to_class(y, 2.975, 3.975)
    acc = float((ct == cp).mean())
    recs = {l: round(float((cp[ct == l] == l).mean()) * 100, 1) for l in ["低", "中", "高"]}
    print(f"Tuned thresholds: 低<{cut_low_mid}<=中<{cut_mid_high}<=高  "
          f"acc={acc*100:.1f}%  召回={recs}")

    # holdout 再验证一次（带权）
    Xtr, Xte, ytr, yte, wtr, _ = train_test_split(X, y, w, test_size=0.2, random_state=42)
    holdout = xgb.XGBRegressor(**params).fit(Xtr, ytr, sample_weight=wtr)
    yp = holdout.predict(Xte)
    print(f"Holdout :  MAE={mean_absolute_error(yte, yp):.4f}  R2={r2_score(yte, yp):.4f}")

    # 用全量数据训练最终模型（带权）
    print("\nTraining final model on full data ...")
    model = xgb.XGBRegressor(**params).fit(X, y, sample_weight=w)

    os.makedirs(MODELS_DIR, exist_ok=True)
    model_path = os.path.join(MODELS_DIR, "model.json")
    model.get_booster().save_model(model_path)
    print(f"  saved {model_path}")

    # ---- 元数据 ----
    # 各维度样本归一化均值（雷达图基准线）
    dim_baseline: dict[str, float] = {}
    cols = list(df.columns)
    for sec in schema.SECTIONS:
        for dim in sec.dimensions:
            arr = df[[cols[c] for c in dim.columns]].to_numpy(dtype=float)
            dim_baseline[dim.key] = round(float(arr.mean()) / sec.scale, 4)

    # 分类阈值已由 tune_thresholds 基于 OOF 预测搜索得到（cut_low_mid / cut_mid_high）
    cls_series = pd.Series(cls)

    metadata = {
        "feature_names": feat_names,
        "n_features": len(feat_names),
        "target": "满意度均分",
        "metrics": {
            "cv_mae": round(cv_mae, 4),
            "cv_r2": round(cv_r2, 4),
            "cv_acc": round(acc, 4),
            "cv_recall": recs,
            "n_train": int(len(df)),
        },
        "model_type": "XGBoostRegressor",
        "sample_weighting": {
            "strength": WEIGHT_STRENGTH,
            "high_boost": WEIGHT_HIGH_BOOST,
        },
        "score_range": [1, 5],
        "sample_stats": {
            "mean": round(float(y.mean()), 4),
            "std": round(float(y.std()), 4),
            "min": round(float(y.min()), 4),
            "max": round(float(y.max()), 4),
        },
        "class_thresholds": {"low_mid": cut_low_mid, "mid_high": cut_mid_high},
        "class_distribution": cls_series.value_counts().to_dict(),
        "dimension_baseline": dim_baseline,
        "dimension_names": schema.DIMENSION_NAMES,
        "dimension_scale": schema.DIMENSION_SCALE,
    }
    meta_path = os.path.join(MODELS_DIR, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"  saved {meta_path}")
    print(f"\nClass thresholds: low<{cut_low_mid}<=mid<{cut_mid_high}<=high")
    print("Done.")


if __name__ == "__main__":
    main()
