import logging
import sys
from pathlib import Path

logger = logging.getLogger()

# create formatter
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(message)s",
)

# Ensure logs directory exists
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# create handlers
stream_handler = logging.StreamHandler(sys.stdout)
file_handler = logging.FileHandler(log_dir / "app.log")

# set formatters
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add handlers to the logger
logger.handlers = [stream_handler, file_handler]

# set log-level
logger.setLevel(logging.INFO)

# Silence watchfiles spam
logging.getLogger("watchfiles").propagate = False