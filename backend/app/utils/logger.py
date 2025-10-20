import logging
import sys
from pathlib import Path

# create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s",
)

# create handlers
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

# Try to add file handler, but continue without it if it fails
handlers = [stream_handler]

# Ensure logs directory exists and try to create file handler
log_dir = Path("logs")
try:
    log_dir.mkdir(exist_ok=True, parents=True)
    file_handler = logging.FileHandler(log_dir / "app.log")
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
except (PermissionError, OSError) as e:
    # Log to stdout only if file logging fails
    print(f"Warning: Cannot write to log file ({e}), logging to stdout only", file=sys.stderr)

# Initialize logger
logger = logging.getLogger()
logger.handlers = handlers

# set log-level
logger.setLevel(logging.INFO)

# Silence watchfiles spam
logging.getLogger("watchfiles").propagate = False