"""
Modellarni ONNX formatiga o'tkazish.

Chiqish:
    models/xgboost.onnx         — XGBoost klassifikator
    models/isolation_forest.onnx — Isolation Forest anomaliya detektori
    models/pipeline_meta.json    — feature nomlari va versiya

Ishlatish: python scripts/10_export_onnx.py
"""

import json
import os
import pickle
import sys
import numpy as np
import pandas as pd

MODEL_DIR = "models"


def load_pkl(name: str):
    path = os.path.join(MODEL_DIR, name)
    if not os.path.exists(path):
        sys.stderr.write(f"   XATO: {path} topilmadi\n")
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


# ─── 1. XGBoost → ONNX ───────────────────────────────────────────────────────

sys.stderr.write("1. XGBoost → ONNX...\n")
xgb_bundle = load_pkl("xgboost_model.pkl")

if xgb_bundle:
    import onnxmltools
    from onnxmltools.convert import convert_xgboost
    from onnxmltools.convert.common.data_types import FloatTensorType

    xgb_model = xgb_bundle["model"]
    features  = xgb_bundle["features"]
    n_feats   = len(features)

    initial_type = [("float_input", FloatTensorType([None, n_feats]))]
    xgb_onnx = convert_xgboost(
        xgb_model,
        initial_types=initial_type,
        target_opset=12,
    )

    xgb_path = os.path.join(MODEL_DIR, "xgboost.onnx")
    with open(xgb_path, "wb") as f:
        f.write(xgb_onnx.SerializeToString())

    size_kb = os.path.getsize(xgb_path) / 1024
    sys.stderr.write(f"   Saqlandi: {xgb_path} ({size_kb:.1f} KB)\n")
    XGB_OK = True
else:
    XGB_OK = False


# ─── 2. IsolationForest → ONNX ───────────────────────────────────────────────

sys.stderr.write("2. IsolationForest → ONNX...\n")
iso_bundle = load_pkl("isolation_forest.pkl")

if iso_bundle:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType

    iso_model  = iso_bundle["model"]
    features   = iso_bundle["features"]
    n_feats    = len(features)

    initial_type = [("float_input", FloatTensorType([None, n_feats]))]
    iso_onnx = convert_sklearn(
        iso_model,
        initial_types=initial_type,
        target_opset={"": 12, "ai.onnx.ml": 3},
    )

    iso_path = os.path.join(MODEL_DIR, "isolation_forest.onnx")
    with open(iso_path, "wb") as f:
        f.write(iso_onnx.SerializeToString())

    size_kb = os.path.getsize(iso_path) / 1024
    sys.stderr.write(f"   Saqlandi: {iso_path} ({size_kb:.1f} KB)\n")
    ISO_OK = True
else:
    ISO_OK = False


# ─── 3. Scaler → ONNX ────────────────────────────────────────────────────────

sys.stderr.write("3. Scaler → ONNX...\n")
bundle = xgb_bundle or iso_bundle
if bundle and "scaler" in bundle:
    from skl2onnx import convert_sklearn
    from skl2onnx.common.data_types import FloatTensorType

    scaler    = bundle["scaler"]
    features  = bundle["features"]
    n_feats   = len(features)

    initial_type = [("float_input", FloatTensorType([None, n_feats]))]
    sc_onnx = convert_sklearn(scaler, initial_types=initial_type,
                               target_opset={"": 12, "ai.onnx.ml": 3})

    sc_path = os.path.join(MODEL_DIR, "scaler.onnx")
    with open(sc_path, "wb") as f:
        f.write(sc_onnx.SerializeToString())
    size_kb = os.path.getsize(sc_path) / 1024
    sys.stderr.write(f"   Saqlandi: {sc_path} ({size_kb:.1f} KB)\n")
    SC_OK = True
else:
    SC_OK = False


# ─── 4. Meta JSON ─────────────────────────────────────────────────────────────

sys.stderr.write("4. Meta ma'lumotlar yozilmoqda...\n")
meta = {
    "version": "1.0.0",
    "project": "AuksionWatch",
    "training_data": "Fergana.xlsx (weak-supervision, 114 lot)",
    "features": (xgb_bundle or iso_bundle or {}).get("features", []),
    "n_features": len((xgb_bundle or iso_bundle or {}).get("features", [])),
    "models": {
        "xgboost": {
            "file": "xgboost.onnx",
            "type": "XGBClassifier",
            "cv_auc": (xgb_bundle or {}).get("cv_auc"),
            "cv_ap":  (xgb_bundle or {}).get("cv_ap"),
            "output": "probability [0..1], threshold 0.5",
        },
        "isolation_forest": {
            "file": "isolation_forest.onnx",
            "type": "IsolationForest",
            "contamination": 0.12,
            "output": "anomaly score (higher = more anomalous)",
        },
        "scaler": {
            "file": "scaler.onnx",
            "type": "StandardScaler",
            "note": "apply before inference",
        },
    },
    "inference_order": ["scaler → isolation_forest", "scaler → xgboost"],
    "risk_ensemble": "rule×0.40 + xgb_prob×0.35 + iso_norm×0.25",
}

meta_path = os.path.join(MODEL_DIR, "pipeline_meta.json")
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
sys.stderr.write(f"   Saqlandi: {meta_path}\n")


# ─── 5. ONNX INFERENCE TEST ───────────────────────────────────────────────────

sys.stderr.write("\n5. Inference test...\n")
try:
    import onnxruntime as ort

    # Test input: 1 ta namuna (barcha feature'lar = 0.5)
    features  = (xgb_bundle or iso_bundle)["features"]
    X_test    = np.random.rand(3, len(features)).astype(np.float32)

    # Scaler test
    if SC_OK:
        sc_sess  = ort.InferenceSession(sc_path)
        X_scaled = sc_sess.run(None, {"float_input": X_test})[0]
        sys.stderr.write(f"   Scaler: {X_test.shape} → {X_scaled.shape} OK\n")
    else:
        X_scaled = X_test

    # XGBoost test
    if XGB_OK:
        xgb_sess = ort.InferenceSession(xgb_path)
        xgb_out  = xgb_sess.run(None, {"float_input": X_scaled})
        probs    = xgb_out[1]  # [N, 2] probabilities
        sys.stderr.write(f"   XGBoost: probabilities shape={np.array(probs).shape}, sample={np.array(probs)[0]} OK\n")

    # IsoForest test
    if ISO_OK:
        iso_sess = ort.InferenceSession(iso_path)
        iso_out  = iso_sess.run(None, {"float_input": X_scaled})
        sys.stderr.write(f"   IsoForest: labels={iso_out[0][:3]} OK\n")

    sys.stderr.write("   Barcha modellar ONNX runtime'da ishlaydi\n")

except Exception as e:
    sys.stderr.write(f"   Inference test xatosi: {e}\n")


# ─── 6. FAYL HAJMLARI ────────────────────────────────────────────────────────

sys.stderr.write("\n" + "=" * 50 + "\n")
sys.stderr.write("ONNX fayllari:\n")
for fname in ["xgboost.onnx", "isolation_forest.onnx", "scaler.onnx", "pipeline_meta.json"]:
    fpath = os.path.join(MODEL_DIR, fname)
    if os.path.exists(fpath):
        kb = os.path.getsize(fpath) / 1024
        sys.stderr.write(f"  {fname:<30} {kb:>8.1f} KB\n")

pkl_xgb = os.path.getsize(os.path.join(MODEL_DIR, "xgboost_model.pkl")) / 1024
pkl_iso = os.path.getsize(os.path.join(MODEL_DIR, "isolation_forest.pkl")) / 1024
sys.stderr.write(f"\nSolishturuv (pickle):\n")
sys.stderr.write(f"  xgboost_model.pkl              {pkl_xgb:>8.1f} KB\n")
sys.stderr.write(f"  isolation_forest.pkl           {pkl_iso:>8.1f} KB\n")
sys.stderr.write("=" * 50 + "\n")
