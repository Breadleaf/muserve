import subprocess

if __name__ == "__main__":
    popen = subprocess.Popen(
        ["python", "Server.py"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    try:
        for line in iter(popen.stdout.readline, ""):
            print(f"server output (out): {line.strip()}")
        for line in iter(popen.stderr.readline, ""):
            print(f"server output (err): {line.strip()}")
    except KeyboardInterrupt:
        print("shutting down server...")
        popen.stdin.write("shutdown\n")
        popen.stdin.flush()
        popen.wait()
    finally:
        popen.stdout.close()
        popen.stderr.close()
        popen.wait()
