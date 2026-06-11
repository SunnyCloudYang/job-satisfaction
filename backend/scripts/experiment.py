"""对比多种建模方案，挑选最优配置。

所有候选都用同一份 5 折 out-of-fold 预测评估，保证公平、无过拟合虚高。
关注指标：MAE / RMSE / R²、两端偏差（低估/高估）、三档召回（尤其"高"档）。

候选：
  A baseline        当前线上配置
  B weighted        样本按真实分到均值的距离加权（拉抬两端）
  C deeper          更深的树 + 更小 min_child_weight，增强尾部拟合
  D weighted+deeper B 与 C 结合
  E monotone        在 D 基础上加单调约束（公平/忠诚维度正向）

用法:
    python backend/scripts/experiment.py [path/to/data.xlsx]
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold

HERE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.dirname(HERE)
sys.path.insert(0, BACKEND)
from app import schema  # noqa: E402
from scripts.train import DEFAULT_DATA, build_matrix  # noqa: E402

BASE = dict(
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

DEEPER = {**BASE, "max_depth": 5, "min_child_weight": 2, "n_estimators": 600,
          "learning_rate": 0.04, "reg_lambda": 2.0}


def make_weights(y: np.ndarray, strength: float = 1.0, high_boost: float = 1.6) -> np.ndarray:
    """离均值越远权重越大；高分样本额外加权（样本稀少）。"""
    mu = y.mean()
    w = 1.0 + strength * np.abs(y - mu) / y.std()
    w[y >= 3.975] *= high_boost  # 高档样本稀少，额外抬权
    return w


def monotone_constraints() -> str:
    """公平/忠诚/认同维度对满意度设正向单调；人口学不约束。"""
    feat = schema.feature_names()
    cons = []
    for name in feat:
        cons.append(0 if name.startswith("demo.") else 1)
    return "(" + ",".join(str(c) for c in cons) + ")"


def oof_predict(params: dict, X, y, sample_weight=None) -> np.ndarray:
    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    pred = np.zeros_like(y, dtype=float)
    for tr, te in kf.split(X):
        m = xgb.XGBRegressor(**params)
        if sample_weight is not None:
            m.fit(X[tr], y[tr], sample_weight=sample_weight[tr])
        else:
            m.fit(X[tr], y[tr])
        pred[te] = m.predict(X[te])
    return np.clip(pred, 1.0, 5.0)


def to_class(v, lo=2.975, hi=3.975):
    out = np.full(v.shape, "中", dtype=object)
    out[v < lo] = "低"
    out[v >= hi] = "高"
    return out


def report(name: str, y, yp) -> dict:
    mae = mean_absolute_error(y, yp)
    rmse = float(np.sqrt(mean_squared_error(y, yp)))
    r2 = r2_score(y, yp)
    # 两端偏差
    low_bias = float((yp - y)[y < 2.0].mean())
    high_bias = float((yp - y)[y >= 4.5].mean())
    # 各档召回
    ct, cp = to_class(y), to_class(yp)
    rec = {}
    for l in ["低", "中", "高"]:
        m = ct == l
        rec[l] = float((cp[m] == l).mean()) if m.sum() else 0.0
    acc = float((ct == cp).mean())
    print(f"{name:<16} MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f} "
          f"| 低估(高分){high_bias:+.3f} 高估(低分){low_bias:+.3f} "
          f"| acc={acc*100:4.1f}% 召回 低{rec['低']*100:4.1f} 中{rec['中']*100:4.1f} 高{rec['高']*100:4.1f}")
    return dict(name=name, mae=mae, rmse=rmse, r2=r2, acc=acc, rec=rec,
               low_bias=low_bias, high_bias=high_bias, yp=yp)


def tune_thresholds(y, yp):
    """网格搜索让三档 macro-recall 最优的阈值。"""
    ct = to_class(y)
    best = None
    for lo in np.arange(2.6, 3.21, 0.025):
        for hi in np.arange(3.55, 4.21, 0.025):
            if hi <= lo:
                continue
            cp = to_class(yp, lo, hi)
            recs = []
            for l in ["低", "中", "高"]:
                m = ct == l
                recs.append((cp[m] == l).mean() if m.sum() else 0)
            macro = float(np.mean(recs))
            acc = float((ct == cp).mean())
            score = macro  # 优先平衡各档召回
            if best is None or score > best[0]:
                best = (score, lo, hi, acc, recs)
    return best


def main():
    data_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DATA
    print(f"Loading {data_path} ...")
    df = pd.read_excel(data_path)
    X, y, _ = build_matrix(df)
    print(f"  samples={len(y)}  features={X.shape[1]}\n")

    w = make_weights(y)
    mono = monotone_constraints()

    results = []
    print("================ 候选方案对比（5 折 OOF）================")
    results.append(report("A baseline", y, oof_predict(BASE, X, y)))
    results.append(report("B weighted", y, oof_predict(BASE, X, y, w)))
    results.append(report("C deeper", y, oof_predict(DEEPER, X, y)))
    results.append(report("D weighted+deep", y, oof_predict(DEEPER, X, y, w)))
    results.append(report("E +monotone", y,
                          oof_predict({**DEEPER, "monotone_constraints": mono}, X, y, w)))

    # 温和加权梯度：在 baseline 参数上，看 strength/high_boost 的折中
    print("\n---- 温和加权梯度（baseline 参数）----")
    for s, hb in [(0.4, 1.2), (0.6, 1.3), (0.8, 1.4)]:
        wm = make_weights(y, strength=s, high_boost=hb)
        results.append(report(f"F w(s={s},hb={hb})", y, oof_predict(BASE, X, y, wm)))

    # 选 MAE 最小且 R2 不显著下降者作为回归最优；同时报告高档召回
    best_reg = min(results, key=lambda r: r["mae"])
    print(f"\n回归综合最优(按 MAE): {best_reg['name']}")

    # 对 baseline 和最优回归分别做阈值调优，看分类能改善多少
    print("\n================ 阈值调优（让三档召回更均衡）================")
    for r in [results[0], best_reg]:
        sc, lo, hi, acc, recs = tune_thresholds(y, r["yp"])
        print(f"{r['name']:<16} 最优阈值 低<{lo:.3f}<=中<{hi:.3f}<=高  "
              f"-> acc={acc*100:.1f}% 召回 低{recs[0]*100:.1f} 中{recs[1]*100:.1f} 高{recs[2]*100:.1f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
