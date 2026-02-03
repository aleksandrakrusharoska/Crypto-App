package mk.ukim.finki.das.prototype.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;


@Entity
@Table(name = "historical_data")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Record {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    private String symbol;

    private LocalDate date;

    private Double open;
    private Double high;
    private Double low;
    private Double close;

    @Column(name = "volume_from")
    private Double volumeFrom;

    @Column(name = "volume_to")
    private Double volumeTo;
}
