"""预测服务：加载 XGBoost 模型，输出与前端契约一致的预测结果。

返回结构（对齐 frontend PredictionResult）:
  {
    score, level, levelLabel, percentile,
    dimensions: [{key,name,mean,max,normalized,sampleNormalized}],
    contributions: [{key,name,value}],
    advice: [str]
  }
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import xgboost as xgb

from . import schema
from .advice import ADVICE_TEMPLATES, POSITIVE_ADVICE

MODELS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")

LEVEL_LABEL = {"low": "低满意度", "mid": "中满意度", "high": "高满意度"}


class Predictor:
    def __init__(self, models_dir: str = MODELS_DIR):
        self.models_dir = models_dir
        self.booster: xgb.Booster | None = None
        self.meta: dict = {}
        self._feature_index: dict[str, int] = {}
        self.load()

    def load(self) -> None:
        model_path = os.path.join(self.models_dir, "model.json")
        meta_path = os.path.join(self.models_dir, "metadata.json")
        if not (os.path.exists(model_path) and os.path.exists(meta_path)):
            raise FileNotFoundError(
                f"Model files not found in {self.models_dir}. Run scripts/train.py first."
            )
        self.booster = xgb.Booster()
        self.booster.load_model(model_path)
        with open(meta_path, encoding="utf-8") as f:
            self.meta = json.load(f)
        self._feature_index = {n: i for i, n in enumerate(self.meta["feature_names"])}

    @property
    def ready(self) -> bool:
        return self.booster is not None

    # ---- helpers ----

    def _level(self, score: float) -> str:
        t = self.meta["class_thresholds"]
        if score < t["low_mid"]:
            return "low"
        if score < t["mid_high"]:
            return "mid"
        return "high"

    def _percentile(self, score: float) -> int:
        """基于样本正态近似估算百分位 (1-99)。"""
        st = self.meta["sample_stats"]
        mu, sd = st["mean"], max(st["std"], 1e-6)
        z = (score - mu) / sd
        cdf = 0.5 * (1 + math.erf(z / math.sqrt(2)))
        return int(min(99, max(1, round(cdf * 100))))

    def _dimensions(self, answers: dict) -> list[dict]:
        means = schema.dimension_means(answers)
        baseline = self.meta["dimension_baseline"]
        names = self.meta["dimension_names"]
        scale = self.meta["dimension_scale"]
        out = []
        for key, m in means.items():
            mx = scale[key]
            out.append(
                {
                    "key": key,
                    "name": names[key],
                    "mean": round(m, 3),
                    "max": mx,
                    "normalized": round(m / mx, 4),
                    "sampleNormalized": baseline.get(key, 0.55),
                }
            )
        return out

    def _contributions(self, vec: np.ndarray) -> list[dict]:
        """用 SHAP (pred_contribs) 把题目级贡献聚合到维度级。"""
        dmat = xgb.DMatrix(vec.reshape(1, -1), feature_names=self.meta["feature_names"])
        # 最后一列是 bias，去掉
        contribs = self.booster.predict(dmat, pred_contribs=True)[0][:-1]

        agg: dict[str, float] = {}
        for fname, val in zip(self.meta["feature_names"], contribs):
            # 仅聚合 Likert 题目（demo.* 单独不展示在贡献图）
            if fname.startswith("demo."):
                key = "demographics"
            else:
                # 形如 justice.distributive.0 -> distributive
                key = fname.split(".")[1]
            agg[key] = agg.get(key, 0.0) + float(val)

        names = self.meta["dimension_names"]
        out = [
            {"key": k, "name": names.get(k, "人口学因素" if k == "demographics" else k), "value": round(v, 4)}
            for k, v in agg.items()
            if k != "demographics"  # 人口学贡献通常很小，隐藏以聚焦量表维度
        ]
        out.sort(key=lambda d: abs(d["value"]), reverse=True)
        return out

    def _advice(self, dimensions: list[dict]) -> list[str]:
        # 取低于样本基准、差距最大的前 3 个维度
        gaps = [
            (d["key"], d["sampleNormalized"] - d["normalized"])
            for d in dimensions
            if d["normalized"] < d["sampleNormalized"]
        ]
        gaps.sort(key=lambda x: x[1], reverse=True)
        advice = [ADVICE_TEMPLATES[k] for k, _ in gaps[:3] if k in ADVICE_TEMPLATES]
        if not advice:
            advice.append(POSITIVE_ADVICE)
        return advice

    # ---- public ----

    def predict(self, answers: dict) -> dict:
        vec = np.asarray(schema.answers_to_vector(answers), dtype=float)
        dmat = xgb.DMatrix(vec.reshape(1, -1), feature_names=self.meta["feature_names"])
        raw = float(self.booster.predict(dmat)[0])
        lo, hi = self.meta["score_range"]
        score = round(min(hi, max(lo, raw)), 2)

        level = self._level(score)
        dimensions = self._dimensions(answers)

        return {
            "score": score,
            "level": level,
            "levelLabel": LEVEL_LABEL[level],
            "percentile": self._percentile(score),
            "dimensions": dimensions,
            "contributions": self._contributions(vec),
            "advice": self._advice(dimensions),
        }

    def model_info(self) -> dict:
        return {
            "model_type": self.meta.get("model_type"),
            "target": self.meta.get("target"),
            "metrics": self.meta.get("metrics"),
            "n_features": self.meta.get("n_features"),
            "score_range": self.meta.get("score_range"),
            "class_thresholds": self.meta.get("class_thresholds"),
        }

    def sample_stats(self) -> dict:
        return {
            "sample_stats": self.meta.get("sample_stats"),
            "class_distribution": self.meta.get("class_distribution"),
            "dimension_baseline": self.meta.get("dimension_baseline"),
            "dimension_names": self.meta.get("dimension_names"),
            "dimension_scale": self.meta.get("dimension_scale"),
        }
