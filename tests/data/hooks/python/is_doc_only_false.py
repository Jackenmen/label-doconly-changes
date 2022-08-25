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

# === remove shebang and docstring ===
# --- BEFORE ---
#!/usr/bin/python
"""module docstring"""


def func():
    ...
# --- AFTER ----



def func():
    ...
# ===


# [COMMENTS]
# === remove shebang and add docstring ===
# --- BEFORE ---
#!/usr/bin/python


def func():
    ...
# --- AFTER ----
"""module docstring"""


def func():
    ...
# ===

# === remove comment in a function and add docstring ===
# --- BEFORE ---
def func():
    # some code comment
    ...
# --- AFTER ----
def func():
    """function docstring"""
    ...
# ===

# === remove comment in a class and add docstring ===
# --- BEFORE ---
class Foo:
    # some code comment
    ...
# --- AFTER ----
class Foo:
    """class docstring"""
    ...
# ===

# === edit comment in a class and add docstring ===
# --- BEFORE ---
class Foo:
    # some code comment
    ...
# --- AFTER ----
class Foo:
    # different code comment
    """class docstring"""
    ...
# ===

# === edit comment in a class ===
# --- BEFORE ---
class Foo:
    # some code comment
    """class docstring"""
    ...
# --- AFTER ----
class Foo:
    # different code comment
    """class docstring"""
    ...
# ===
