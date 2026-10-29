import pyautogui
import cv2
import numpy as np
from ultralytics import YOLO
import time
import threading
import mss

stop_flag = threading.Event()

try:
    from pynput import keyboard

    def on_press(key):
        if key == keyboard.Key.space:
            print("\n⏹ Пробел нажат — аварийная остановка...")
            stop_flag.set()
            return False

    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    print("✅ Слушатель пробела запущен (глобально).")
except ImportError:
    print("⚠️ pynput не установлен. Установите: pip install pynput")
except Exception as e:
    print(f"⚠️ Не удалось запустить слушатель: {e}")

# Загрузка модели (ONNX)
model = YOLO('best.onnx')

CLASSES = {0: "game", 1: "upgrade", 2: "advertising"}
CONF_THRESHOLD = 0.35

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.01

sct = mss.mss()

# Захватываем весь основной монитор (monitor 1 = основной, 0 = все мониторы вместе)
CAPTURE_REGION = sct.monitors[1]
print(f"Область захвата (весь экран): {CAPTURE_REGION}")


def click_safe(x, y, clicks=1):
    """Клик с проверкой stop_flag и границ экрана."""
    if stop_flag.is_set():
        return False
    try:
        sw, sh = pyautogui.size()
        if 0 <= x < sw and 0 <= y < sh:
            pyautogui.click(x, y, clicks=clicks, interval=0.02)
            return True
    except Exception:
        pass
    return False


def process_game(capture_region):
    if stop_flag.is_set():
        return False

    left = capture_region["left"]
    top = capture_region["top"]

    try:
        screenshot = sct.grab(capture_region)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
    except Exception:
        return False

    if stop_flag.is_set():
        return False

    try:
        results = model(frame, verbose=False)
    except Exception:
        return False

    if stop_flag.is_set():
        return False

    found = []
    for result in results:
        for box in result.boxes:
            conf = float(box.conf[0])
            if conf < CONF_THRESHOLD:
                continue
            x1, y1, x2, y2 = map(float, box.xyxy[0])
            cls_id = int(box.cls[0])
            cls_name = CLASSES.get(cls_id)
            if cls_name is None:
                continue

            found.append({
                "class": cls_name,
                "cx": (x1 + x2) / 2.0,
                "cy": (y1 + y2) / 2.0,
                "x1": x1, "y1": y1, "x2": x2, "y2": y2,
                "conf": conf,
                "abs_x": int(left + (x1 + x2) / 2.0),
                "abs_y": int(top + (y1 + y2) / 2.0),
            })

    if not found:
        return False

    # 1. РЕКЛАМА (закрываем в первую очередь)
    for obj in [o for o in found if o["class"] == "advertising"]:
        if stop_flag.is_set():
            return False
        if click_safe(obj["abs_x"], obj["abs_y"]):
            print(f"❌ Реклама закрыта: ({obj['abs_x']}, {obj['abs_y']})")
            # Ждём, но прерываемся, если нажат пробел
            for _ in range(80):
                if stop_flag.is_set():
                    return True
                time.sleep(0.01)
            return True

    # 2. ПЕЧЕНЬКА
    cookies = [o for o in found if o["class"] == "game"]
    if cookies:
        if stop_flag.is_set():
            return False
        best = max(cookies, key=lambda o: o["conf"])
        if click_safe(best["abs_x"], best["abs_y"], clicks=5):
            print(f"🎯 Клик по печеньке: ({best['abs_x']}, {best['abs_y']})")
            return True

    return False


# === ГЛАВНЫЙ БЛОК ===
print("Бот запущен. Остановка: ПРОБЕЛ (глобально, в любой момент).")
print("Захватывается весь основной экран. Убедись, что игра видна на экране.")

try:
    while not stop_flag.is_set():
        try:
            acted = process_game(CAPTURE_REGION)
            if stop_flag.is_set():
                break
            time.sleep(0.05 if acted else 0.3)
        except pyautogui.FailSafeException:
            print("\n🛑 Аварийная остановка (мышь в углу).")
            break
        except Exception as e:
            print(f"⚠️ Ошибка в цикле: {e}")
            time.sleep(0.5)
except Exception:
    pass

try:
    listener.stop()
except Exception:
    pass

print("✅ Бот остановлен.")