import os

# Before any app import: in-memory DB, mock hardware, no background poll
os.environ.update(ADAPTER="mock", DB_PATH=":memory:", POLL_SECONDS="0")
