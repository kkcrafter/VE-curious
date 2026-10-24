"""Reservation state machine. Pure: no DB, no hardware.

The transition table in docs/design/state-machine.md wins if this differs.
G3 tickets (#21-#25) add their rows here.
"""

TERMINAL = ("COMPLETED", "CANCELLED", "NO_SHOW", "FAILED", "FAULT_REPORTED")

# (state, event) -> next state
TRANSITIONS = {
    ("SCHEDULED", "reserve_ok"): "RESERVED",  # slot start reached, hardware hold done
    ("SCHEDULED", "reserve_failed"): "FAILED",
    ("SCHEDULED", "cancel"): "CANCELLED",
    ("REQUESTED", "reserve_ok"): "RESERVED",
    ("REQUESTED", "reserve_failed"): "FAILED",
    ("RESERVED", "cancel"): "CANCELLED",
    ("RESERVED", "plate_match"): "ARRIVED",
    ("ARRIVED", "start_charging"): "CHARGING",  # [GAP C3] driver tap until Ecurious gives a signal
    ("CHARGING", "stop_charging"): "COMPLETED",
    ("CHARGING", "vehicle_left"): "COMPLETED",
}

# Events a driver can send through the API; the others come from hardware or timers
DRIVER_ACTIONS = ("cancel", "report_fault", "confirm_arrival", "deny_arrival", "start_charging", "stop_charging")

# Hardware call made when entering a state. RESERVED has none: reserve runs before reserve_ok.
EFFECTS = {"ARRIVED": "unlock", "CANCELLED": "release", "COMPLETED": "release"}


def next_state(state, event):
    return TRANSITIONS.get((state, event))


def allowed_actions(state):
    return [event for (s, event) in TRANSITIONS if s == state and event in DRIVER_ACTIONS]
