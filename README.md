Smart‑PyInstaller
---
Простой консольный сборщик EXE для Python‑проектов.

Использование
---

Вариант 1 – из папки 

1. Поместите Smart‑Pyinstaller.py в папку проекта (рядом с main.py).
2. Поместите ярлык в тот же проект, это может быть ico сразу,если не ico то сконвертируется в него.
3. Запустите: python Smart‑Pyinstaller.py
4. Ответьте на вопросы – готовый exe появится в папке dist.

Вариант 2 – через IDE (PyCharm и др.)

1. Откройте проект в PyCharm, убедитесь что выбран проект который нужен.
2. Откройте встроенный терминал (Alt+F12)
3. Ярлык должен быть сразу помешён в проект.
4. Выполните команду: python Smart‑Pyinstaller.py
5. Ответьте на вопросы – итоговый exe в папке dist.

Возможности
---

· Автоопределение main.py (или выбор другого скрипта).

· Конвертация PNG/JPG/BMP/WEBP в .ico (если установлен Pillow).

· Настройка консоли (--noconsole) и прав администратора (--uac-admin).

· Автоматическое добавление --collect-all=customtkinter при обнаружении.

· Очистка временных файлов (build/, временная иконка), но .spec сохраняется при ошибке для отладки.

· Корректные коды возврата (0 – успех, ненулевые – ошибки) для CI/CD.

Требования
---

· Python 3.6+

· PyInstaller: pip install pyinstaller

· Pillow (опционально, для иконок): pip install pillow


Smart‑PyInstaller
---

A simple console‑based EXE builder for Python projects.

Usage
---

Option 1 – from project folder

1. Place Smart‑Pyinstaller.py in your project folder (next to main.py).
2. Put your icon in the same folder – it can be a .ico file directly, or another image (PNG/JPG/etc.) which will be converted automatically.
3. Run: python Smart‑Pyinstaller.py
4. Answer the prompts – the final .exe will appear in the dist folder.

Option 2 – via IDE (PyCharm)

1. Open your project in PyCharm and make sure the correct interpreter (with venv) is selected.
2. Open the built‑in terminal (Alt+F12).
3. Place the icon in the project folder beforehand.
4. Run: python Smart‑Pyinstaller.py
5. Answer the prompts – the final .exe will be in the dist folder.

Feature
---

· Auto‑detects main.py (or lets you choose another script).

· Converts PNG/JPG/BMP/WEBP images to .ico (if Pillow is installed).

· Console mode (--noconsole) and admin rights (--uac-admin) configurable.

· Automatically adds --collect-all=customtkinter if customtkinter is imported.

· Cleans up temporary files (build/, temp icon), but keeps the .spec file on build failure for debugging.

· Proper exit codes (0 = success, non‑zero = errors) for CI/CD usage.

Requirement
---

· Python 3.6+

· PyInstaller: pip install pyinstaller

· Pillow (optional, for icon conversion): pip install pillow
