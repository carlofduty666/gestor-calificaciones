#!/usr/bin/env python
"""Script para comentar todos los @login_required en admin.py"""

import re

admin_path = 'app/routes/admin.py'

# Leer archivo
with open(admin_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Procesar líneas
new_lines = []
commented_count = 0

for line in lines:
    # Si la línea es exactamente @login_required (con espacios al inicio)
    if line.strip() == '@login_required':
        # Preservar indentación
        indent = len(line) - len(line.lstrip())
        new_lines.append(' ' * indent + '# @login_required  # DEMO MODE: comentado temporalmente\n')
        commented_count += 1
    else:
        new_lines.append(line)

print(f"[OK] Comentados {commented_count} instancias de @login_required")

# Escribir archivo
with open(admin_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f"[✓] Archivo {admin_path} actualizado exitosamente")
