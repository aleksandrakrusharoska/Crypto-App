package mk.ukim.finki.das.app.model.entity;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;


@Entity
@Table(name = "coins")
@Data
@AllArgsConstructor
@NoArgsConstructor
public class Coin {

    @Id
    private String symbol;

    private String fullName;
}
