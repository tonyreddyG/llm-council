import logging

class LogFilter(logging.Filter):
    """Filter out noise/waste errors from logs."""
    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        # Kill the 401 Unauthorized noise for /api/me check (startup probe)
        if " /api/me " in msg and " 401 " in msg:
            return False
        # Kill the login retry noise (expected if user isn't registered yet)
        if " /api/login " in msg and " 401 " in msg:
            if record.levelno <= logging.INFO:
                return False
        # Kill the Windows connection reset noise
        if "ConnectionResetError" in msg or "WinError 10054" in msg:
            return False
        if "_ProactorBasePipeTransport" in msg:
            return False
        return True

def setup_logging():
    """Apply filters to uvicorn loggers."""
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.addFilter(LogFilter())

def custom_loop_exception_handler(loop, context):
    """Suppress specific asyncio loop tracebacks that pollute the logs."""
    exception = context.get("exception")
    if exception and (isinstance(exception, ConnectionResetError) or "WinError 10054" in str(exception)):
        return
    loop.default_exception_handler(context)
