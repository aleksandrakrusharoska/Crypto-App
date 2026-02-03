from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.service.lstm_service import run_training
from app.state.training_state import training_state, TrainingStatus

router = APIRouter(prefix="/api")


@router.post("/predict/{symbol}", status_code=202)
def start_prediction(symbol: str, background_tasks: BackgroundTasks):
    state = training_state.get(symbol)

    if state and state["status"] in (
            TrainingStatus.STARTED,
            TrainingStatus.RUNNING
    ):
        return {
            "symbol": symbol,
            "status": state["status"]
        }

    training_state[symbol] = {
        "status": TrainingStatus.STARTED,
        "message": "Training queued"
    }

    background_tasks.add_task(run_training, symbol)

    return {
        "symbol": symbol,
        "status": TrainingStatus.STARTED
    }


@router.get("/predict/{symbol}")
def get_prediction(symbol: str):
    state = training_state.get(symbol)

    if not state or state["status"] in (
            TrainingStatus.STARTED,
            TrainingStatus.RUNNING
    ):
        raise HTTPException(
            status_code=202,
            detail="Training in progress"
        )

    if state["status"] == TrainingStatus.FAILED:
        raise HTTPException(
            status_code=500,
            detail=state.get("message", "Training failed")
        )

    return state.get("result")


@router.get("/predict/{symbol}/status")
def get_prediction_status(symbol: str):
    if symbol not in training_state:
        return {
            "symbol": symbol,
            "status": TrainingStatus.IDLE
        }

    return {
        "symbol": symbol,
        **training_state[symbol]
    }
