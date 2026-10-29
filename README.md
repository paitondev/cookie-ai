# Cookie Clicker Ai

Бот для автоматической игры в Cookie Clicker с использованием YOLO-детекции и `mss` для быстрых скриншотов. Работает на Linux (X11), не требует `sudo` и `xdotool`.

## Возможности

Автоматический клик по печеньке (класс `game`)
Автоматическое закрытие рекламы (класс `advertising`)
Глобальная аварийная остановка по клавише **Пробел**
Защита от кликов за границами экрана и после остановки

## Зависимости

```bash
pip install mss pyautogui opencv-python numpy ultralytics pynput onnxruntime