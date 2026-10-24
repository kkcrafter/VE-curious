# <Team name> – Smart Reservation for Public EV Charging

Covers deliverables 3 (process documentation) and 5 (limitations and scaling).

## 1. Summary

What we built in three sentences. Which mission areas we answered.

## 2. Architecture

Diagram: app ↔ our backend ↔ Ecurious server ↔ hardware; GoingElectric.

| Component | Responsibility | Technology |
|---|---|---|
| | | |

## 3. Reservation cycle

State machine (link or diagram). Sequence of the full cycle: reserve → arrive → charge → release.

## 4. API calls

| Call | Direction | Endpoint / method | Request | Response | Notes |
|---|---|---|---|---|---|
| | | | | | |

## 5. Data flows

What data goes where, when.

## 6. Design decisions

Link to decision log. Key decisions with reason and rejected alternatives.

## 7. Mission areas

### 7.x <Area>
Problem → our answer → how we demo it → open points.

## 8. GDPR

| Data item | Purpose | Where stored | Retention | Legal basis / consent |
|---|---|---|---|---|
| License plate | Check-in, blocked-bay detection | | | |
| Location / GPS | ETA, no-show detection | | | |
| Account (name, email) | Booking, notifications | | | |
| Payment | Fees | | | |

Note: a hash of a plate is pseudonymised, not anonymous (plates are guessable).

## 9. Business case and KPIs

Pricing parameters: reservation fee, no-show fee, no-show cap, grace period, subscription, revenue share.

KPIs for CPOs: occupancy, no-show rate, blocked minutes, reservations per bay per day, utilisation change.

Label all simulated numbers as assumptions.

## 10. What did not work

| Time | What we tried | What happened | What we did instead |
|---|---|---|---|
| | | | |

## 11. Limitations and scaling

Other apps, other operators, other locations and hardware. Standards (OCPP, OCPI).

## 12. Tools and sources

See declaration log.
