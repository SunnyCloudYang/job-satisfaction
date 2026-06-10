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
from sklearn.model_selection import KFold, cross_val_predict, train_test_split

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from app import schema  # noqa: E402

MODELS_DIR = os.path.join(BACKEND, "models")
DEFAULT_DATA = "/Volumes/WenshuSpace/软著数据.xlsx"


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

    # 5 折交叉验证评估泛化能力
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    cv_pred = cross_val_predict(xgb.XGBRegressor(**params), X, y, cv=kf)
    cv_mae = mean_absolute_error(y, cv_pred)
    cv_r2 = r2_score(y, cv_pred)
    print(f"\n5-fold CV:  MAE={cv_mae:.4f}  R2={cv_r2:.4f}")

    # holdout 再验证一次
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    holdout = xgb.XGBRegressor(**params).fit(Xtr, ytr)
    yp = holdout.predict(Xte)
    print(f"Holdout :  MAE={mean_absolute_error(yte, yp):.4f}  R2={r2_score(yte, yp):.4f}")

    # 用全量数据训练最终模型
    print("\nTraining final model on full data ...")
    model = xgb.XGBRegressor(**params).fit(X, y)

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

    # 分类阈值：用数据中各类别的均分边界推断
    cls_series = pd.Series(cls)
    thresholds = {}
    for label in ["低", "中", "高"]:
        sub = y[cls_series.to_numpy() == label]
        if len(sub):
            thresholds[label] = [round(float(sub.min()), 3), round(float(sub.max()), 3)]
    # 低/中、中/高 切分点（取相邻类别边界中点）
    low_hi = thresholds.get("低", [1, 2])[1]
    mid_lo = thresholds.get("中", [2, 3])[0]
    mid_hi = thresholds.get("中", [3, 4])[1]
    high_lo = thresholds.get("高", [4, 5])[0]
    cut_low_mid = round((low_hi + mid_lo) / 2, 3)
    cut_mid_high = round((mid_hi + high_lo) / 2, 3)

    metadata = {
        "feature_names": feat_names,
        "n_features": len(feat_names),
        "target": "满意度均分",
        "metrics": {
            "cv_mae": round(cv_mae, 4),
            "cv_r2": round(cv_r2, 4),
            "n_train": int(len(df)),
        },
        "model_type": "XGBoostRegressor",
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
