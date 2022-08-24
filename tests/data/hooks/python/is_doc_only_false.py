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


# [FUNCTIONS]
# === modified return value ===
# --- BEFORE ---
def func(x, y):
    return x + y
# --- AFTER ----
def func(x, y):
    return x - y
# ===

# --- BEFORE ---
def func(x, y):
    """function docstring"""
    return x + y
# --- AFTER ----
def func(x, y):
    """function docstring"""
    return x - y
# ===


# === modified docstring *and* return value ===
# --- BEFORE ---
def func(x, y):
    """function docstring"""
    return x + y
# --- AFTER ----
def func(x, y):
    """changed docstring"""
    return x - y
# ===


# [CLASSES]
# === modified attribute value ===
# --- BEFORE ---
class Foo:
    BAR = "BAZ"
# --- AFTER ----
class Foo:
    BAR = "FOO"
# --- BEFORE ---
class Foo:
    BAR = "BAZ"
# --- AFTER ----
class Foo:
    BAR = "FOO"
# ===

# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAZ"
# --- AFTER ----
class Foo:
    """class docstring"""

    BAR = "FOO"
# ===


# === modified docstring *and* attribute value ===
# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAZ"
# --- AFTER ----
class Foo:
    """changed docstring"""

    BAR = "FOO"
# ===


# [WHITESPACE]
# === whitespace modified without docstring removal ===
# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAR"
# --- AFTER ----
class Foo:
    """changed docstring"""


    BAR = "BAR"
# ===
