import sys
with open("test.txt", "w") as f:
    f.write("Python is working.\n")
    try:
        import requests
        f.write("requests: OK\n")
    except ImportError as e:
        f.write(f"requests: FAIL {e}\n")
    
    try:
        import bs4
        f.write("bs4: OK\n")
    except ImportError as e:
        f.write(f"bs4: FAIL {e}\n")
    
    try:
        import playwright
        f.write("playwright: OK\n")
    except ImportError as e:
        f.write(f"playwright: FAIL {e}\n")
