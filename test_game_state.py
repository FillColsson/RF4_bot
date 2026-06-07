"""
Live demo of vision-driven game state detection.
Run: python test_game_state.py
"""
import json
import os
import cv2
import mss
import numpy as np

from vision.game_state import GameStateAnalyzer, GamePhase


def load_config():
    if os.path.exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    with open("config.example.json", "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    config = load_config()
    analyzer = GameStateAnalyzer(config)
    sct = mss.mss()
    monitor = sct.monitors[1]
    region = config.get("detection_region", {})

    print("Vision Game State Demo — ESC to exit")
    print("Train with: python utils/train_vision.py")

    while True:
        shot = sct.grab(monitor)
        frame = np.array(shot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        x, y = region.get("x", 0), region.get("y", 0)
        w, h = region.get("width", 400), region.get("height", 300)
        roi = frame[y:y + h, x:x + w]

        analysis = analyzer.analyze(frame, roi)
        display = cv2.resize(frame, (960, 540))

        sx = 960 / frame.shape[1]
        sy = 540 / frame.shape[0]
        cv2.rectangle(
            display,
            (int(x * sx), int(y * sy)),
            (int((x + w) * sx), int((y + h) * sy)),
            (0, 255, 0), 2,
        )

        color = (200, 200, 200)
        if analysis.phase == GamePhase.BITE:
            color = (0, 0, 255)
        elif analysis.phase == GamePhase.CATCH_SCREEN:
            color = (0, 255, 255)
        elif analysis.phase == GamePhase.FIGHTING:
            color = (0, 140, 255)

        lines = [
            f"Phase: {analysis.phase.value}",
            f"Bite: {analysis.bite} ({analysis.bite_confidence:.2f})",
            f"Catch screen: {analysis.catch_screen} ({analysis.catch_confidence:.2f})",
            f"Float stable frames: {analysis.float_stable_frames}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(display, line, (10, 30 + i * 28),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, color, 2)

        cv2.imshow("Game State Vision", display)
        if cv2.waitKey(1) & 0xFF == 27:
            break

    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
