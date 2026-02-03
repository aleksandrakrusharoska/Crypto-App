package mk.ukim.finki.das.app.service;


import mk.ukim.finki.das.app.model.dto.lstm.PredictionResponse;
import mk.ukim.finki.das.app.model.enums.TrainingStatus;

public interface LstmService {
    void startTraining(String symbol);

    PredictionResponse getPrediction(String symbol);

    TrainingStatus getStatus(String symbol);

}
