package mk.ukim.finki.das.app.model.dto.lstm;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PredictionResponse {

    private String symbol;
    private String prediction_date;
    private Double predicted_close;
    private Double rmse;
    private Double mae;
    private Double mape;
    private Double r2;

}
