import sys
print(f"Python Executable: {sys.executable}")
print(f"Sys Path: {sys.path}")
try:
    import pandas
    print(f"Pandas Version: {pandas.__version__}")
    print(f"Pandas Path: {pandas.__file__}")
except ImportError as e:
    print(f"ImportError: {e}")
