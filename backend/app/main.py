"""Flask 应用：工作满意度预测 API。"""
from __future__ import annotations

import logging

from flask import Flask, jsonify, request
from flask_cors import CORS

from .predictor import Predictor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jsp")


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)  # 允许前端跨域调用

    # 启动即加载模型（失败也不让进程崩溃，便于排查）
    predictor: Predictor | None = None
    try:
        predictor = Predictor()
        logger.info("Model loaded. metrics=%s", predictor.model_info().get("metrics"))
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to load model: %s", exc)

    def require_model():
        if predictor is None or not predictor.ready:
            return jsonify({"error": "model_not_loaded", "message": "模型未加载，请先运行训练脚本。"}), 503
        return None

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "model_loaded": bool(predictor and predictor.ready)})

    @app.get("/api/model_info")
    def model_info():
        err = require_model()
        if err:
            return err
        return jsonify(predictor.model_info())

    @app.get("/api/sample_stats")
    def sample_stats():
        err = require_model()
        if err:
            return err
        return jsonify(predictor.sample_stats())

    @app.post("/api/predict")
    def predict():
        err = require_model()
        if err:
            return err
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            return jsonify({"error": "bad_request", "message": "请求体需为 JSON 对象。"}), 400
        answers = payload.get("answers", payload)
        if not isinstance(answers, dict):
            return jsonify({"error": "bad_request", "message": "answers 字段需为对象。"}), 400
        try:
            result = predictor.predict(answers)
        except Exception as exc:  # noqa: BLE001
            logger.exception("predict failed")
            return jsonify({"error": "predict_failed", "message": str(exc)}), 500
        return jsonify(result)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
