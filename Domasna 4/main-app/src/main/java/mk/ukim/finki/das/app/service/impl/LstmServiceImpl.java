package mk.ukim.finki.das.app.service.impl;

import mk.ukim.finki.das.app.model.dto.lstm.PredictionResponse;
import mk.ukim.finki.das.app.model.enums.TrainingStatus;
import mk.ukim.finki.das.app.model.exceptions.LstmTrainingException;
import mk.ukim.finki.das.app.service.LstmService;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.List;
import java.util.Map;


@Service
public class LstmServiceImpl implements LstmService {

    private final RestTemplate restTemplate;

    @Value("${lstm.service.url}")
    private String lstmServiceUrl;

    public LstmServiceImpl(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }


    @Override
    public void startTraining(String symbol) {
        String url = lstmServiceUrl + "/api/predict/" + symbol;

        HttpHeaders headers = new HttpHeaders();
        headers.setAccept(List.of(MediaType.APPLICATION_JSON));

        HttpEntity<Void> entity = new HttpEntity<>(headers);

        restTemplate.exchange(
                url,
                HttpMethod.POST,
                entity,
                Void.class
        );
    }

    @Override
    public PredictionResponse getPrediction(String symbol) {

        TrainingStatus status = getStatus(symbol);

        if (status == TrainingStatus.RUNNING || status == TrainingStatus.STARTED) {
            throw new LstmTrainingException(
                    TrainingStatus.RUNNING,
                    "Training in progress"
            );
        }

        if (status == TrainingStatus.FAILED) {
            throw new LstmTrainingException(
                    TrainingStatus.FAILED,
                    "Training failed"
            );
        }

        if (status == TrainingStatus.ERROR) {
            throw new LstmTrainingException(
                    TrainingStatus.ERROR,
                    "Prediction service unavailable"
            );
        }

        String url = lstmServiceUrl + "/api/predict/" + symbol;

        ResponseEntity<PredictionResponse> response =
                restTemplate.getForEntity(url, PredictionResponse.class);

        if (!response.getStatusCode().is2xxSuccessful()) {
            throw new LstmTrainingException(
                    TrainingStatus.FAILED,
                    "Prediction endpoint error"
            );
        }

        if (response.getBody() == null) {
            throw new LstmTrainingException(
                    TrainingStatus.FAILED,
                    "Prediction missing"
            );
        }

        return response.getBody();
    }


    @Override
    public TrainingStatus getStatus(String symbol) {

        String url = lstmServiceUrl + "/api/predict/" + symbol + "/status";

        try {
            ResponseEntity<Map> response =
                    restTemplate.getForEntity(url, Map.class);

            return TrainingStatus.valueOf(
                    response.getBody().get("status").toString()
            );

        } catch (Exception e) {
            return TrainingStatus.ERROR;
        }

    }


}
