"""结构化日志 + 关联 ID — 追踪请求全链路。

每个请求分配唯一 correlation_id，所有日志都带上它，方便排查问题。
"""

import logging
import json
import sys
from contextvars import ContextVar

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """JSON 格式日志，方便日志聚合工具解析。"""

    def format(self, record):
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_var.get(""),
        }
        if record.exc_info and record.exc_info[0]:
            log_data["exception"] = self.formatException(record.exc_info)

        for key in ("model", "agent_id", "user_id", "latency_ms", "error_type"):
            if hasattr(record, key):
                log_data[key] = getattr(record, key)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(json_format: bool = True):
    """初始化日志配置。"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if json_format:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        ))

    root_logger.handlers = [handler]
