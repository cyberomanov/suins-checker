import requests


def execute_change_ip(change_ip_url: str) -> bool:
    if change_ip_url:
        response = requests.get(url=change_ip_url)
        if response.status_code == 200:
            return True
        else:
            return False
