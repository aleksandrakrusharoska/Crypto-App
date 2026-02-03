package mk.ukim.finki.das.prototype.repository;

import mk.ukim.finki.das.prototype.model.entity.Coin;
import org.springframework.data.jpa.repository.JpaRepository;

public interface CoinRepository extends JpaRepository<Coin, String> {
}
