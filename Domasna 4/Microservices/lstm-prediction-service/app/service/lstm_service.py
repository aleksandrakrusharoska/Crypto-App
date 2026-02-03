from app.state.training_state import training_state, TrainingStatus
from ml.lstm_train import train_lstm_for_symbol


def run_training(symbol: str):
    try:
        print(f"[LSTM] START {symbol}", flush=True)

        training_state[symbol]["status"] = TrainingStatus.RUNNING
        training_state[symbol]["message"] = "Training in progress"

        result = train_lstm_for_symbol(symbol)

        training_state[symbol]["result"] = result
        training_state[symbol]["status"] = TrainingStatus.DONE
        training_state[symbol]["message"] = "Training finished"

        print(f"[LSTM] DONE {symbol}", flush=True)

    except Exception as e:
        training_state[symbol]["status"] = TrainingStatus.FAILED
        training_state[symbol]["message"] = str(e)
        training_state[symbol].pop("result", None)

