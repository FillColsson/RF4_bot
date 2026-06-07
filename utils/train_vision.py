"""
Обучение vision-системы на скриншотах из игры.

Запуск: python utils/train_vision.py

Горячие клавиши:
  1 — спокойный поплавок (ожидание)
  2 — поклёвка
  3 — экран улова
  4 — вываживание
  C — сохранить шаблон экрана улова (catch_samples/)
  T — пересчитать профиль vision_profile.json
  S — сохранить текущий кадр в training_samples/
  ESC — выход
"""
import json
import os
import sys
from datetime import datetime

import cv2
import mss
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from vision.game_state import GameStateAnalyzer, GamePhase


LABELS = {
    ord("1"): "float_calm",
    ord("2"): "bite",
    ord("3"): "catch_screen",
    ord("4"): "fighting",
}


def load_config():
    path = "config.json"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    with open("config.example.json", "r", encoding="utf-8") as f:
        return json.load(f)


def crop_region(frame, region):
    x = region.get("x", 0)
    y = region.get("y", 0)
    w = region.get("width", frame.shape[1])
    h = region.get("height", frame.shape[0])
    return frame[y:y + h, x:x + w]


def save_sample(frame, label, out_dir="training_samples"):
    os.makedirs(out_dir, exist_ok=True)
    name = f"{label}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.png"
    path = os.path.join(out_dir, name)
    cv2.imwrite(path, frame)
    print(f"✓ Образец [{label}]: {path}")
    return path


def save_catch_template(frame, out_dir="catch_samples"):
    os.makedirs(out_dir, exist_ok=True)
    h, w = frame.shape[:2]
    roi = frame[int(h * 0.1):int(h * 0.9), int(w * 0.15):int(w * 0.85)]
    name = f"catch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    path = os.path.join(out_dir, name)
    cv2.imwrite(path, roi)
    print(f"✓ Шаблон улова: {path}")
    return path


def compute_profile(samples_dir="training_samples"):
    """Build vision_profile.json from labeled catch_screen samples."""
    catch_files = []
    if os.path.isdir(samples_dir):
        for name in os.listdir(samples_dir):
            if name.startswith("catch_screen"):
                catch_files.append(os.path.join(samples_dir, name))

    if not catch_files:
        print("⚠️  Нет образцов catch_screen в training_samples/ (нажми 3 во время улова)")
        return False

    features = []
    for path in catch_files:
        img = cv2.imread(path)
        if img is None:
            continue
        h, w = img.shape[:2]
        roi = img[int(h * 0.1):int(h * 0.9), int(w * 0.15):int(w * 0.85)]
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        features.append([
            hsv[:, :, 0].mean(),
            hsv[:, :, 1].mean(),
            hsv[:, :, 2].mean(),
            gray.mean(),
        ])

    arr = np.array(features)
    profile = {
        "catch_screen_stats": {
            "mean": arr.mean(axis=0).tolist(),
            "std": arr.std(axis=0).tolist(),
            "samples": len(features),
        },
        "catch_screen_threshold": 0.5,
        "catch_edge_ratio": 0.82,
        "trained_at": datetime.now().isoformat(),
    }

    with open("vision_profile.json", "w", encoding="utf-8") as f:
        json.dump(profile, f, indent=2, ensure_ascii=False)

    print(f"✓ Профиль сохранён: vision_profile.json ({len(features)} образцов)")
    return True


def draw_overlay(display, analysis, config):
    region = config.get("detection_region", {})
    x, y = region.get("x", 0), region.get("y", 0)
    w, h = region.get("width", 0), region.get("height", 0)

    scale_x = display.shape[1] / config.get("_frame_w", display.shape[1])
    scale_y = display.shape[0] / config.get("_frame_h", display.shape[0])

    rx, ry = int(x * scale_x), int(y * scale_y)
    rw, rh = int(w * scale_x), int(h * scale_y)
    cv2.rectangle(display, (rx, ry), (rx + rw, ry + rh), (0, 255, 0), 2)

    phase = analysis.phase.value
    color = (200, 200, 200)
    if analysis.phase == GamePhase.BITE:
        color = (0, 0, 255)
    elif analysis.phase == GamePhase.CATCH_SCREEN:
        color = (0, 255, 255)
    elif analysis.phase == GamePhase.FIGHTING:
        color = (0, 165, 255)
    elif analysis.phase == GamePhase.FLOAT_CALM:
        color = (0, 255, 0)

    cv2.putText(display, f"Phase: {phase}", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
    cv2.putText(display, f"Bite: {analysis.bite} ({analysis.bite_confidence:.2f})", (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    cv2.putText(display, f"Catch: {analysis.catch_screen} ({analysis.catch_confidence:.2f})", (10, 85),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 1)
    cv2.putText(display, f"Float stable: {analysis.float_stable_frames}", (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

    if analysis.float_info and analysis.float_info.get("position"):
        pos = analysis.float_info["position"]
        sx = int(pos[0] * scale_x) + rx
        sy = int(pos[1] * scale_y) + ry
        cv2.circle(display, (sx, sy), 8, (0, 255, 0), 2)

    help_y = display.shape[0] - 10
    cv2.putText(display, "1=calm 2=bite 3=catch 4=fight C=template T=train ESC=exit",
                (10, help_y), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (150, 150, 150), 1)


def main():
    config = load_config()
    analyzer = GameStateAnalyzer(config)
    sct = mss.mss()
    monitor = sct.monitors[1]

    print("=" * 60)
    print("ОБУЧЕНИЕ VISION-СИСТЕМЫ RF4")
    print("=" * 60)
    print("Играй в RF4 и нажимай клавиши когда видишь нужный момент:")
    print("  1 — поплавок спокоен")
    print("  2 — поклёвка")
    print("  3 — экран улова")
    print("  4 — вываживание")
    print("  C — шаблон улова")
    print("  T — обучить профиль")
    print("  ESC — выход")
    print("=" * 60)

    while True:
        shot = sct.grab(monitor)
        frame = np.array(shot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        config["_frame_w"] = frame.shape[1]
        config["_frame_h"] = frame.shape[0]

        region = config.get("detection_region", {})
        roi = crop_region(frame, region)
        analysis = analyzer.analyze(frame, roi)

        display = cv2.resize(frame, (960, 540))
        draw_overlay(display, analysis, config)
        cv2.imshow("RF4 Vision Training", display)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            break
        elif key in LABELS:
            save_sample(frame, LABELS[key])
        elif key in (ord("c"), ord("C")):
            save_catch_template(frame)
        elif key in (ord("t"), ord("T")):
            if compute_profile():
                analyzer.reload_profile()
        elif key in (ord("s"), ord("S")):
            save_sample(frame, analysis.phase.value)

    cv2.destroyAllWindows()
    print("Готово.")


if __name__ == "__main__":
    main()
