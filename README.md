# smart-pyinstaller

A simple console-based EXE builder for Python projects.

## Usage
1. Place `Sm-Pyinstaller.py` in your project folder (next to `main.py`).
2. Place the icon next to Sm-Pyinstaller.py (in the folder).
3. Run: ` Sm-Pyinstaller.py`
4. Answer the prompts (EXE name, console mode, admin rights).
5. The final `.exe` will appear in the `dist` folder.

## Features
- Automatically finds `main.py`
- Converts PNG/JPG images to `.ico` (if Pillow is installed)
- Configurable console display and admin privileges
- Auto-cleaning of temporary files (`build`, `.spec`)

## Requirements
- Python 3.6+
- PyInstaller: `pip install pyinstaller`
- Pillow (optional): `pip install pillow` (for icon conversion)



# smart-pyinstaller

Простой консольный сборщик EXE для Python-проектов.

## Использование
1. Поместите `Sm-Pyinstaller.py` в папку с вашим проектом (рядом с `main.py`).
2. Поместите иконку рядом с Sm-Pyinstaller.py (в папку)
3. Запустите: `Sm-Pyinstaller.py`
4. Ответьте на вопросы (имя EXE, консоль, админ).
5. Готовый `.exe` появится в папке `dist`.

## Возможности
- Автоматический поиск `main.py`
- Конвертация PNG/JPG в `.ico` (если установлен Pillow)
- Настройка консоли и прав администратора
- Авто-очистка временных файлов (`build`, `.spec`)

## Требования
- Python 3.6+
- PyInstaller: `pip install pyinstaller`
- Pillow (опционально): `pip install pillow` (для конвертации иконок)
