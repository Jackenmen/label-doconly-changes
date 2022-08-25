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


# [FUNCTIONS]
# === identical contents ===
# --- BEFORE ---
def func(x, y):
    return x + y
# --- AFTER ----
def func(x, y):
    return x + y
# ===

# --- BEFORE ---
def func(x, y):
    """function docstring"""
    return x + y
# --- AFTER ----
def func(x, y):
    """function docstring"""
    return x + y
# ===


# === modified docstring ===
# --- BEFORE ---
def func(x, y):
    """function docstring"""
    return x + y
# --- AFTER ----
def func(x, y):
    """changed docstring"""
    return x + y
# ===


# === removal of a docstring ===
# --- BEFORE ---
def func(x, y):
    """function docstring"""
    return x + y
# --- AFTER ----
def func(x, y):
    return x + y
# ===


# [CLASSES]
# === identical contents ===
# --- BEFORE ---
class Foo:
    BAR = "BAR"
# --- AFTER ----
class Foo:
    BAR = "BAR"
# ===

# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAR"
# --- AFTER ----
class Foo:
    """class docstring"""

    BAR = "BAR"
# ===


# === modified docstring ===
# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAR"
# --- AFTER ----
class Foo:
    """changed docstring"""

    BAR = "BAR"
# ===


# === removal of a docstring ===
# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAR"
# --- AFTER ----
class Foo:

    BAR = "BAR"
# ===


# [WHITESPACE]
# === removal of a class docstring ===
# --- BEFORE ---
class Foo:
    """class docstring"""

    BAR = "BAR"
# --- AFTER ----
class Foo:
    BAR = "BAR"
# ===

# === remove module docstring without removing the line it's in ===
# --- BEFORE ---
"""module docstring"""


def func():
    ...
# --- AFTER ----



def func():
    ...
# ===

# === a lot of whitespace added with a docstring ===
# --- BEFORE ---
class Foo:
    BAR = "BAR"
# --- AFTER ----
class Foo:


    """changed docstring"""


    BAR = "BAR"
# ===

# === docstring addition using line continuation and implicit concatenation ===
# --- BEFORE ---
class Foo:
    BAR = "BAR"
# --- AFTER ----
class Foo:
    """hmm""" \
    \
    """changed docstring"""


    BAR = "BAR"
# ===


# [COMMENTS]
# === add a class docstring before a comment ===
# --- BEFORE ---
class Foo:
    # some code comment
    ...
# --- AFTER ----
class Foo:
    """class docstring"""
    # some code comment
    ...
# ===

# === add a class docstring after a comment ===
# --- BEFORE ---
class Foo:
    # some code comment
    ...
# --- AFTER ----
class Foo:
    # some code comment
    """class docstring"""
    ...
# ===
