"""量表 schema —— 后端的唯一真相源，与前端 questions.ts 严格对齐。

特征向量按以下顺序构造（与训练时一致）：
  demographics(one-hot) + justice(20) + loyalty(17) + identity(6)

前端提交的 answers 使用 `${sectionId}.${dimKey}.${j}` 作为题目键，
本模块负责把它展开成模型可用的特征向量。
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dimension:
    key: str
    name: str
    n_items: int
    # 原始 Excel 中该维度题目对应的列索引（用于训练）
    columns: tuple[int, ...]


@dataclass(frozen=True)
class Section:
    id: str
    title: str
    scale: int  # 量表满分（5 或 7）
    dimensions: list[Dimension] = field(default_factory=list)


# ---- Likert 量表三大部分（不含工作满意度，因为它是预测目标） ----

JUSTICE = Section(
    id="justice",
    title="组织公平感",
    scale=7,
    dimensions=[
        Dimension("distributive", "分配公平", 4, tuple(range(31, 35))),
        Dimension("procedural", "程序公平", 7, tuple(range(35, 42))),
        Dimension("interpersonal", "人际公平", 4, tuple(range(42, 46))),
        Dimension("informational", "信息公平", 5, tuple(range(46, 51))),
    ],
)

LOYALTY = Section(
    id="loyalty",
    title="主管忠诚",
    scale=7,
    dimensions=[
        Dimension("dedication", "奉献", 4, tuple(range(54, 58))),
        Dimension("effort", "努力", 3, tuple(range(58, 61))),
        Dimension("following", "跟随", 4, tuple(range(61, 65))),
        Dimension("identification", "认同主管", 3, tuple(range(65, 68))),
        Dimension("internalization", "内化主管价值观", 3, tuple(range(68, 71))),
    ],
)

IDENTITY = Section(
    id="identity",
    title="组织认同感",
    scale=5,
    dimensions=[
        Dimension("identity", "组织认同感", 6, tuple(range(74, 80))),
    ],
)

SECTIONS: list[Section] = [JUSTICE, LOYALTY, IDENTITY]

# 维度中文名映射（结果展示用）
DIMENSION_NAMES: dict[str, str] = {
    d.key: d.name for s in SECTIONS for d in s.dimensions
}

# 每个维度所属量表满分
DIMENSION_SCALE: dict[str, int] = {
    d.key: s.scale for s in SECTIONS for d in s.dimensions
}

# ---- 人口学信息 ----
# 训练 / 预测时统一 one-hot。类别取值与前端 demographics 一致。
DEMOGRAPHICS: dict[str, list[str]] = {
    "gender": ["女", "男"],
    "marital": ["未婚/离异", "已婚/同居"],
    "police_type": ["刑警", "治安警", "交巡警", "户籍警", "社区警", "其他"],
}

# 原始 Excel 中人口学列索引
DEMO_COLUMNS = {"gender": 3, "marital": 4, "police_type": 5}

# 目标列
TARGET_MEAN_COL = 28  # 满意度均分 (1-5 连续)
TARGET_CLASS_COL = 29  # 满意度分类 (低/中/高)


def likert_feature_names() -> list[str]:
    """所有 Likert 题目的特征名，顺序固定。"""
    names: list[str] = []
    for sec in SECTIONS:
        for dim in sec.dimensions:
            for j in range(dim.n_items):
                names.append(f"{sec.id}.{dim.key}.{j}")
    return names


def demographic_feature_names() -> list[str]:
    """人口学 one-hot 特征名，顺序固定。"""
    names: list[str] = []
    for key, cats in DEMOGRAPHICS.items():
        for cat in cats:
            names.append(f"demo.{key}.{cat}")
    return names


def feature_names() -> list[str]:
    """完整特征顺序：人口学 one-hot + 所有 Likert 题目。"""
    return demographic_feature_names() + likert_feature_names()


N_LIKERT = sum(d.n_items for s in SECTIONS for d in s.dimensions)  # 43
N_FEATURES = len(feature_names())


def answers_to_vector(answers: dict) -> list[float]:
    """把前端提交的 answers 转成模型输入向量。

    answers 形如:
      {
        "gender": "男", "marital": "已婚/同居", "police_type": "刑警",
        "justice.distributive.0": 5, ...
      }
    缺失题目按量表中值填充，缺失人口学按全 0（未知）。
    """
    vec: list[float] = []

    # 人口学 one-hot
    for key, cats in DEMOGRAPHICS.items():
        val = answers.get(key)
        for cat in cats:
            vec.append(1.0 if val == cat else 0.0)

    # Likert
    for sec in SECTIONS:
        mid = (sec.scale + 1) / 2.0
        for dim in sec.dimensions:
            for j in range(dim.n_items):
                raw = answers.get(f"{sec.id}.{dim.key}.{j}")
                try:
                    v = float(raw)
                except (TypeError, ValueError):
                    v = mid
                # 约束在合法范围
                v = max(1.0, min(float(sec.scale), v))
                vec.append(v)

    return vec


def dimension_means(answers: dict) -> dict[str, float]:
    """各维度原始均分（用于雷达图与建议）。"""
    out: dict[str, float] = {}
    for sec in SECTIONS:
        mid = (sec.scale + 1) / 2.0
        for dim in sec.dimensions:
            vals = []
            for j in range(dim.n_items):
                raw = answers.get(f"{sec.id}.{dim.key}.{j}")
                try:
                    vals.append(float(raw))
                except (TypeError, ValueError):
                    vals.append(mid)
            out[dim.key] = sum(vals) / len(vals) if vals else mid
    return out
