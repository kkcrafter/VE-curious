"""Reservation state machine. Pure: no DB, no hardware.

The transition table in docs/design/state-machine.md wins if this differs.
"""

TERMINAL = ("COMPLETED", "CANCELLED", "NO_SHOW", "FAILED", "FAULT_REPORTED")
