import subprocess
import time
import requests

def start_container(image_uri: str, host_port: int) -> str:
    result = subprocess.run(["docker", "run", "-d", "-p", f"{host_port}:8000", image_uri], capture_output=True, text=True, check=True)

    return result.stdout.strip()

def wait_for_healthy(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            response = requests.get(f"{url}/health", timeout=2)
            if response.status_code == 200:
                return True

        except requests.exceptions.ConnectionError:
            pass

        time.sleep(1)
    return False

def stop_container(container_id: str) -> None:
    subprocess.run(["docker", "stop", container_id], check=True)
