import sys
import os
import requests
import tomllib


class CheckUpdate:
    def __init__(self):
        with open("pyproject.toml", "rb") as f:
            self.pyproject = tomllib.load(f)

    def check_update(self):
        try:
            response = requests.get("")
            response.raise_for_status()
            latest_version = response.json()["tag_name"]
            if latest_version != self.pyproject["project"]["version"]:
                print(f"A new version of MaaSimulator is available: {latest_version}")
                print("Please download the latest version from https://github.com/MaaSimulator/MaaSimulator/releases")
            else:
                print("MaaSimulator is up todate")
                return True
            return False
        except requests.exceptions.RequestException as e:
            print(f"Error checking for updates: {e}")
            return False
