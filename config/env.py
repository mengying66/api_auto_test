import yaml
from pathlib import Path

class Config:
    def __init__(self, env="test_web"):
        self.env = env
        self.config = self._load_config()

    def _load_config(self):
        with open(Path(__file__).parent / "config.yaml", "r") as f:
            return yaml.safe_load(f)[self.env]

    @property
    def base_url(self):
        return self.config["base_url"]

    @property
    def timeout(self):
        return self.config["timeout"]