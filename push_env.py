import os
import subprocess
import sys

def load_env():
    env_vars = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    try:
                        key, value = line.strip().split("=", 1)
                        env_vars[key] = value
                    except ValueError:
                        pass
    return env_vars

def set_railway_vars():
    vars = load_env()
    cmd = ["railway", "variables"]
    
    # Собираем все переменные в одну команду для скорости
    for key, value in vars.items():
        cmd.extend(["--set", f"{key}={value}"])
        
    print(f"Setting variables: {list(vars.keys())}...")
    try:
        subprocess.run(cmd, check=True, shell=True)
        print("Success!")
    except Exception as e:
        print(f"Failed to set variables: {e}")
        print("Make sure you are linked to a project (run 'railway link')")

if __name__ == "__main__":
    set_railway_vars()