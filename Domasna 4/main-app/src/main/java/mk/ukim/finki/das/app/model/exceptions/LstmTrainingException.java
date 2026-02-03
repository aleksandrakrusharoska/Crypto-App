package mk.ukim.finki.das.app.model.exceptions;

import lombok.Getter;
import mk.ukim.finki.das.app.model.enums.TrainingStatus;


@Getter
public class LstmTrainingException extends RuntimeException {
    private final TrainingStatus status;

    public LstmTrainingException(TrainingStatus status, String message) {
        super(message);
        this.status = status;
    }

}

