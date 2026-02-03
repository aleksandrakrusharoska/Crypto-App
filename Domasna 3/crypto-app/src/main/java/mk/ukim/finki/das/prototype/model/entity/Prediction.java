package mk.ukim.finki.das.prototype.model.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

@Entity
@Table(name = "lstm_predictions")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String symbol;

    @Column(name = "prediction_date")
    private LocalDate predictionDate;

    @Column(name = "predicted_close")
    private Double predictedClose;

    private Double rmse;
    private Double mape;
    private Double r2;

}
