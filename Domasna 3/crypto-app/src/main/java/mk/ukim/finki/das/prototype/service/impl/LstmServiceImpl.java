package mk.ukim.finki.das.prototype.service.impl;

import mk.ukim.finki.das.prototype.model.entity.Prediction;
import mk.ukim.finki.das.prototype.model.exceptions.LstmTrainingException;
import mk.ukim.finki.das.prototype.service.LstmService;
import org.springframework.stereotype.Service;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.time.LocalDate;

@Service
public class LstmServiceImpl implements LstmService {

//    private final LstmPredictionRepository predictionRepository;
//
//    public LstmServiceImpl(LstmPredictionRepository predictionRepository) {
//        this.predictionRepository = predictionRepository;
//    }

    @Override
    public Prediction runTraining(String symbol) {
        String predictedValue = null;
        String predictedDate = null;
        boolean notEnoughData = false;

        try {
            ProcessBuilder pb = new ProcessBuilder(
                    "venv\\Scripts\\python.exe",
                    "src\\main\\python\\lstm\\lstm_train.py",
                    symbol
            );
            pb.redirectErrorStream(true);

            Process p = pb.start();

            try (BufferedReader br = new BufferedReader(
                    new InputStreamReader(p.getInputStream()))) {
                String line;
                while ((line = br.readLine()) != null) {
                    System.out.println("[LSTM] " + line);

                    if (line.startsWith("STATUS:NOT_ENOUGH_DATA")) {
                        notEnoughData = true;
                    }

                    if (line.startsWith("DATE:")) {
                        predictedDate = line.replace("DATE:", "").trim();
                    }

                    if (line.startsWith("PREDICTION:")) {
                        predictedValue = line.replace("PREDICTION:", "").trim();
                    }

                }
            }

            int exitCode = p.waitFor();

            if (notEnoughData) {
                throw new LstmTrainingException(
                        "Not enough data to generate prediction for " + symbol
                );
            }

            if (predictedValue == null || predictedDate == null) {
                throw new LstmTrainingException(
                        "Prediction could not be generated."
                );
            }

            System.out.println("LSTM script finished with code: " + exitCode);

            Prediction prediction = new Prediction();
            LocalDate date = LocalDate.parse(predictedDate);
            prediction.setSymbol(symbol);
            prediction.setPredictionDate(date);
            prediction.setPredictedClose(Double.parseDouble(predictedValue));

            return prediction;

        } catch (LstmTrainingException e) {
            throw e;

        } catch (Exception e) {
            throw new LstmTrainingException(
                    "Unexpected error during LSTM training for " + symbol,
                    e
            );
        }


    }

//    @Override
//    public Prediction getLatestPrediction(String symbol) {
//        return predictionRepository
//                .findFirstBySymbolOrderByPredictionDateDesc(symbol)
//                .orElse(null);
//    }
}
