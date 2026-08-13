# 工作满意度预测——公安人员（后端）

基于 XGBoost 回归的工作满意度预测服务。模型以组织公平感、主管忠诚、组织认同感等维度的问卷作答为输入，预测 1–5 分的工作满意度，并通过 SHAP 给出各维度对预测的贡献度与改善建议。

## 技术栈

- Flask 3 + flask-cors —— HTTP 接口
- XGBoost —— 回归模型（`reg:squarederror`）
- SHAP（经由 `booster.predict(pred_contribs=True)`）—— 维度贡献度
- scikit-learn —— 交叉验证

## 目录结构

```
backend/
├── app/
│   ├── schema.py      # 唯一数据契约：维度/题目定义、特征向量构造（与前端 questions.ts 对齐）
│   ├── predictor.py   # 加载模型，输出与前端 PredictionResult 一致的结构
│   ├── advice.py      # 各维度改善建议文案（与前端 predict.ts 一致）
│   └── main.py        # Flask 应用与路由
├── scripts/
│   ├── train.py       # 训练脚本：读 xlsx → 训练 → 保存 model.json / metadata.json
│   ├── inspect_data.py
│   ├── verify_schema.py
│   └── smoke_test.py  # 全 min / mid / max 输入的单调性自检
├── models/
│   ├── model.json     # 训练好的 XGBoost 模型
│   └── metadata.json  # 特征名、指标、样本统计、分级阈值、维度基线
└── requirements.txt
```

## 环境准备

```bash
cd backend
python3 -m venv ../.venv
source ../.venv/bin/activate
pip install -r requirements.txt
# macOS XGBoost 需要 OpenMP 运行时
brew install libomp
```

## 训练模型

模型已随仓库提供（`models/`），通常无需重新训练。如需重训：

```bash
source ../.venv/bin/activate
python scripts/train.py /path/to/软著数据.xlsx
```

当前模型指标（5 折 out-of-fold）：MAE ≈ 0.33，R² ≈ 0.50；训练样本 4271 条。

模型采用样本加权（离均值越远权重越大，并对稀少的高分样本额外加权），
缓解树模型的"向均值回归"，使两端预测更准、高满意度人群更易被识别。
三档阈值（低/中/高）由 OOF 预测自动搜索得到，在整体准确率不低于 65%
的前提下让三档召回尽量均衡（当前各档召回均约 62%–66%）。

## 启动服务

```bash
source ../.venv/bin/activate
python -m app.main           # 开发模式，监听 0.0.0.0:5001

# 生产可用 gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 "app.main:create_app()"
```

## API

所有接口前缀 `/api`，已开启 CORS。

| 方法 | 路径 | 说明 |
|------|------|------|
| GET  | `/api/health`       | 健康检查与模型加载状态 |
| GET  | `/api/model_info`   | 模型指标与元信息 |
| GET  | `/api/sample_stats` | 样本均值/标准差等统计 |
| POST | `/api/predict`      | 提交作答，返回预测结果 |

### POST /api/predict

请求体（`answers` 字段，键为 `sectionId.dimensionKey.itemIndex`，另含人口学字段）：

```json
{
  "answers": {
    "gender": "男",
    "marital": "已婚",
    "police_type": "...",
    "justice.distributive.0": 5,
    "loyalty.dedication.0": 4,
    "identity.identity.0": 4
  }
}
```

响应（与前端 `PredictionResult` 完全一致）：

```json
{
  "score": 3.7,
  "level": "mid",
  "levelLabel": "中满意度",
  "percentile": 75,
  "dimensions": [ { "key": "distributive", "name": "分配公平", "mean": 5.5, "max": 7, "normalized": 0.79, "sampleNormalized": 0.56 } ],
  "contributions": [ { "key": "interpersonal", "name": "人际公平", "value": 0.13 } ],
  "advice": ["..."]
}
```

## 前端联调

前端通过 `PUBLIC_API_BASE` 调用本服务的 `/api/predict` 接口：

```bash
# frontend/.env
PUBLIC_API_BASE=http://127.0.0.1:5001
```

未配置或后端不可达时，前端会显示错误提示。
