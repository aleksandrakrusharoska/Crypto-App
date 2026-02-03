from enum import Enum
from typing import Dict

class TrainingStatus(str, Enum):
    IDLE = "IDLE"
    STARTED = "STARTED"
    RUNNING = "RUNNING"
    DONE = "DONE"
    FAILED = "FAILED"

training_state: Dict[str, dict] = {}
