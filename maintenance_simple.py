import os
import sys
from pathlib import Path

project_root = Path(__file__).parent

def toggle_maintenance(mode):
    lock_file = project_root / 'maintenance.lock'
    if mode == 'on':
        lock_file.touch()
        print("✅ Режим обслуживания ВКЛЮЧЕН")
        print(f"📂 Создан файл: {lock_file}")
    elif mode == 'off':
        if lock_file.exists():
            lock_file.unlink()
            print("✅ Режим обслуживания ВЫКЛЮЧЕН")
        else:
            print("⚠️  Файл maintenance.lock не найден.")
    elif mode == 'status':
        if lock_file.exists():
            print("🔴 Режим обслуживания: ВКЛЮЧЕН")
        else:
            print("🟢 Режим обслуживания: ВЫКЛЮЧЕН")
    else:
        print("Использование: python maintenance_simple.py [on|off|status]")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        toggle_maintenance(sys.argv[1])
    else:
        print("Использование: python maintenance_simple.py [on|off|status]")