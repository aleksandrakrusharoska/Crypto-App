package mk.ukim.finki.das.prototype.model.exceptions;

import org.springframework.http.HttpStatus;
import org.springframework.web.bind.annotation.ResponseStatus;

@ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
public class LstmTrainingException extends RuntimeException {
    public LstmTrainingException(String msg, Throwable cause) {
        super(msg, cause);
    }

    public LstmTrainingException(String msg) {
        super(msg);
    }

}

