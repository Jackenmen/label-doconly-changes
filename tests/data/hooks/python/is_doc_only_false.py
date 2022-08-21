# [MODULES]
# === modified variable value ===
# --- BEFORE ---
x = 1
# --- AFTER ----
x = 2
# ===

# --- BEFORE ---
"""module docstring"""
x = 1
# --- AFTER ----
"""module docstring"""
x = 2
# ===


# === modified docstring *and* variable value ===
# --- BEFORE ---
"""module docstring"""
x = 1
# --- AFTER ----
"""changed docstring"""
x = 2
# ===
