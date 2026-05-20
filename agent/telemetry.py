import json
from datetime import datetime


class TrajectoryLogger:
    def __init__(self, path="trajectory.jsonl"):
        self.path = path

    def log(self, data: dict):
        enriched = {
            "timestamp": datetime.utcnow().isoformat(),
            **data,
        }

        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(enriched) + "\n")