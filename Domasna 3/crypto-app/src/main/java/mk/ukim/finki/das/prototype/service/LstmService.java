package mk.ukim.finki.das.prototype.service;

import mk.ukim.finki.das.prototype.model.entity.Prediction;

public interface LstmService {
    Prediction runTraining(String symbol);
//    Prediction getLatestPrediction(String symbol);
}
