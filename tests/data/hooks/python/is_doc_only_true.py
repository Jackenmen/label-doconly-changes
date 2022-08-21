# [MODULES]
# === identical contents ===
# --- BEFORE ---
x = 1
# --- AFTER ----
x = 1
# ===

# --- BEFORE ---
"""module docstring"""
x = 1
# --- AFTER ----
"""module docstring"""
x = 1
# ===


# === modified docstring ===
# --- BEFORE ---
"""module docstring"""
x = 1
# --- AFTER ----
"""changed docstring"""
x = 1
# ===


# === removal of a docstring ===
# --- BEFORE ---
"""module docstring"""
x = 1
# --- AFTER ----
x = 1
# ===
