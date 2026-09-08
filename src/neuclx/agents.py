"""NeuCLX agents and unified CLISONIX-like agent orchestration layer."""

from __future__ import annotations

import asyncio
import logging
import threading
import time
import unicodedata
import uuid
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Awaitable, Callable, Dict, List, Optional, TypeVar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("AgentSystem")

_AGENT_NAME_ALIASES = {
    "alba": "alba",
    "albi": "albi",
    "jona": "jona",
    "asi": "asi",
    "asitrinity": "asi-trinity",
    "trinity": "asi-trinity",
    "blerina": "blerina",
    "alda": "alda",
    "albana": "albana",
    "dralbana": "albana",
    "mali": "mali",
    "sofia": "sofia",
    "liam": "liam",
    "klajdi": "klajdi",
    "eap": "eap",
    "matia": "matia",
    "videocreator": "video-creator",
    "newspublisher": "news-publisher",
    "selflearning": "selflearning",
    "nanogrid": "nanogrid",
    "zeiss": "zeiss",
}


def normalize_agent_identifier(value: str) -> str:
    """Normalize agent identifiers across unicode, width, accents, and separators."""
    normalized = unicodedata.normalize("NFKC", value or "").strip()
    if not normalized:
        return ""
    collapsed = "".join(
        ch for ch in unicodedata.normalize("NFKD", normalized)
        if not unicodedata.combining(ch)
    )
    key = "".join(ch for ch in collapsed.casefold() if ch.isalnum())
    return _AGENT_NAME_ALIASES.get(key, key)


class AgentStatus(Enum):
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    PAUSED = "paused"
    DRAINING = "draining"
    ERROR = "error"
    TERMINATED = "terminated"


class AgentType(Enum):
    CORE = "core"
    PROCESSING = "processing"
    ANALYTICS = "analytics"
    INTEGRATION = "integration"
    ML = "ml"
    CUSTOM = "custom"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class LoadBalanceStrategy(Enum):
    ROUND_ROBIN = auto()
    LEAST_CONNECTIONS = auto()
    WEIGHTED = auto()
    RANDOM = auto()
    CAPABILITY_MATCH = auto()


T = TypeVar("T")


@dataclass
class AgentConfig:
    name: str
    agent_type: AgentType = AgentType.CUSTOM
    version: str = "1.0.0"
    capabilities: List[str] = field(default_factory=list)
    max_concurrent_tasks: int = 10
    min_instances: int = 1
    max_instances: int = 5
    timeout_seconds: float = 30.0
    retry_count: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 10.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {**asdict(self), "agent_type": self.agent_type.value}


@dataclass
class AgentMetrics:
    agent_id: str
    agent_name: str
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_response_time_ms: float = 0.0
    current_load: int = 0
    uptime_seconds: float = 0.0
    last_heartbeat: Optional[str] = None
    error_rate: float = 0.0

    def update_response_time(self, duration_ms: float):
        alpha = 0.1
        if self.avg_response_time_ms == 0:
            self.avg_response_time_ms = duration_ms
        else:
            self.avg_response_time_ms = alpha * duration_ms + (1 - alpha) * self.avg_response_time_ms

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 100.0
        return (self.completed_tasks / self.total_tasks) * 100


@dataclass
class Task:
    task_id: str
    agent_name: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    timeout: float = 30.0
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __lt__(self, other: "Task") -> bool:
        return self.priority.value < other.priority.value


@dataclass
class TaskResult:
    task_id: str
    agent_id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: float = 0.0
    completed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class BaseAgent(ABC):
    def __init__(self):
        self._id = f"{self.config.name}_{uuid.uuid4().hex[:8]}"
        self._status = AgentStatus.INITIALIZING
        self._metrics = AgentMetrics(agent_id=self._id, agent_name=self.config.name)
        self._start_time = time.time()
        self._current_tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()

    @property
    def id(self) -> str:
        return self._id

    @property
    def status(self) -> AgentStatus:
        return self._status

    @status.setter
    def status(self, value: AgentStatus):
        self._status = value

    @property
    def metrics(self) -> AgentMetrics:
        self._metrics.uptime_seconds = time.time() - self._start_time
        self._metrics.current_load = len(self._current_tasks)
        return self._metrics

    @property
    @abstractmethod
    def config(self) -> AgentConfig:
        pass

    @abstractmethod
    async def execute(self, task: Task) -> Any:
        pass

    async def initialize(self) -> bool:
        self._status = AgentStatus.READY
        logger.info(f"✅ Agent initialized: {self._id}")
        return True

    async def shutdown(self) -> bool:
        self._status = AgentStatus.DRAINING
        while self._current_tasks:
            await asyncio.sleep(0.1)
        self._status = AgentStatus.TERMINATED
        logger.info(f"🛑 Agent shutdown: {self._id}")
        return True

    async def health_check(self) -> Dict[str, Any]:
        return {
            "agent_id": self._id,
            "status": self._status.value,
            "healthy": self._status in [AgentStatus.READY, AgentStatus.BUSY],
            "metrics": asdict(self.metrics),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def can_accept_task(self) -> bool:
        if self._status not in [AgentStatus.READY, AgentStatus.BUSY]:
            return False
        return len(self._current_tasks) < self.config.max_concurrent_tasks

    def has_capability(self, capability: str) -> bool:
        return capability in self.config.capabilities

    async def _run_task(self, task: Task) -> TaskResult:
        start_time = time.time()
        with self._lock:
            self._current_tasks[task.task_id] = task
            self._metrics.total_tasks += 1
        if len(self._current_tasks) > 0:
            self._status = AgentStatus.BUSY
        try:
            result = await asyncio.wait_for(self.execute(task), timeout=task.timeout)
            duration_ms = (time.time() - start_time) * 1000
            self._metrics.completed_tasks += 1
            self._metrics.update_response_time(duration_ms)
            return TaskResult(task_id=task.task_id, agent_id=self._id, success=True, result=result, duration_ms=duration_ms)
        except asyncio.TimeoutError:
            self._metrics.failed_tasks += 1
            return TaskResult(task_id=task.task_id, agent_id=self._id, success=False, error=f"Task timed out after {task.timeout}s", duration_ms=(time.time() - start_time) * 1000)
        except Exception as e:
            self._metrics.failed_tasks += 1
            logger.error(f"Task {task.task_id} failed: {e}")
            return TaskResult(task_id=task.task_id, agent_id=self._id, success=False, error=str(e), duration_ms=(time.time() - start_time) * 1000)
        finally:
            with self._lock:
                self._current_tasks.pop(task.task_id, None)
            if len(self._current_tasks) == 0:
                self._status = AgentStatus.READY


@dataclass(frozen=True)
class AgentAnswer:
    text: str


class AlbaAgent(BaseAgent):
    """Bridge-oriented agent for repository and manifest questions."""

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            name="alba",
            agent_type=AgentType.CORE,
            version="2.0.0",
            capabilities=["bridge", "manifest", "memory", "runtime", "policy"],
            max_concurrent_tasks=20,
            min_instances=1,
            max_instances=5,
        )

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "bridge" in q or "manifest" in q:
            return (
                "Bridge është shtresa e verifikimit të burimeve: ajo ruan manifestin, kontrollon "
                "hash-in, e vërteton evidencën dhe e kalon përmes JONA."
            )
        if "ui" in q or "frontend" in q:
            return "NeuCLX ka një UI të thjeshtë bazuar në server HTTP dhe një app.js të lidhur me /api/respond."
        return "Bridge është pjesa që verifikon burimin, manifestin dhe evidencën përpara se të hyjë në kernel."

    async def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "collect")
        if action == "collect":
            return {
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 62.8,
                    "network_io": {"rx_bytes": 1024000, "tx_bytes": 512000},
                    "active_connections": 128,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "source": self._id,
            }
        if action == "health":
            return {"status": "healthy", "checks": ["api", "memory", "evidence"], "source": self._id}
        return {"status": "unknown_action", "action": action}


class AlbiAgent(BaseAgent):
    """Runtime-oriented agent for runtime and memory questions."""

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            name="albi",
            agent_type=AgentType.CORE,
            version="2.0.0",
            capabilities=["runtime", "memory", "ui", "evidence", "integrations"],
            max_concurrent_tasks=15,
            min_instances=1,
            max_instances=8,
        )

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "ui" in q or "frontend" in q:
            return "Po, ekziston UI në src/neuclx/static me index.html, app.js dhe app.css, dhe aplikacioni ka endpoint /api/respond. Memory është reale dhe përdor SQLite me shënime të verifikuara."
        if "memory" in q:
            return "Memory është reale dhe përdor SQLite me vetëm shënime të verifikuara me state measured/computed."
        if "bridge" in q:
            return "Bridge është shtresa për manifest dhe verifikim të burimit; Albi fokusohet te runtime dhe memory."
        return "NeuCLX ka një runtime real, memory SQLite dhe një UI të thjeshtë, por pa fallback të fshehur."

    async def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "analyze")
        if action == "analyze":
            return {
                "analysis": {
                    "patterns_found": 3,
                    "correlations": [{"field_a": "cpu", "field_b": "memory", "correlation": 0.85}],
                    "insights": ["High correlation between CPU and memory usage"],
                },
                "data_points_analyzed": len(task.payload.get("data", [])) if isinstance(task.payload.get("data", []), list) else 1,
                "analyzed_by": self._id,
            }
        if action == "detect_anomaly":
            return {"anomalies": [{"timestamp": "2026-01-29T10:30:00Z", "severity": "warning", "type": "spike"}], "anomaly_count": 1}
        return {"status": "unknown_action", "action": action}


class JonaAgent(BaseAgent):
    """Policy agent that explains the JONA sandbox boundary."""

    @property
    def config(self) -> AgentConfig:
        return AgentConfig(
            name="jona",
            agent_type=AgentType.CORE,
            version="2.0.0",
            capabilities=["policy", "sandbox", "governance", "security"],
            max_concurrent_tasks=10,
            min_instances=1,
            max_instances=3,
        )

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "sandbox" in q or "policy" in q or "jona" in q:
            return "JONA është sandbox-i obligues i sigurisë dhe policy-ja e kufirit: ai e vlerëson çdo datum para lëshimit dhe ndalon të dhëna të padëshiruara ose jo të verifikuara."
        return "JONA është sandbox-i dhe policy-ja e kufirit të NeuCLX: çdo dalje duhet të kalojë kontrollin e evidencës."

    async def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "synthesize")
        if action == "recommend":
            context = task.payload.get("context", {})
            return {
                "recommendations": [{"priority": "medium", "action": "Consider scaling database", "impact": "high"}],
                "based_on": list(context.keys()) if context else ["general_analysis"],
            }
        if action == "synthesize":
            return {"synthesis": {"key_findings": ["System performance is optimal"], "summary": "Overall system health is good", "confidence": 0.92}, "sources_processed": 1}
        return {"status": "unknown_action", "action": action}


class ALBAAgent(AlbaAgent):
    pass


class ALBIAgent(AlbiAgent):
    pass


class JONAAgent(JonaAgent):
    pass


class ASIAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="asi", agent_type=AgentType.CORE, version="1.0.0", capabilities=["decision-routing", "escalation", "multi-agent-coordination"], max_concurrent_tasks=20, min_instances=1, max_instances=3)

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "route" in q or "agent" in q or "esi" in q:
            return "ASI është shtresa e vendimmarrjes dhe routing-ut: ajo zgjedh agjentin ose rrugën më të përshtatshme për detyrën dhe mund të eskalojë kur duhet."
        return "ASI është shtresa e vendimmarrjes, routing-ut dhe koordinimit multi-agent në NeuCLX."

    async def execute(self, task: Task) -> Any:
        action = task.payload.get("action", "route")
        if action == "route":
            return {"routed_to": "alba", "reason": "metric collection task", "escalated": False}
        return {"status": "unknown_action", "action": action}


class ASITrinityAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="asi-trinity", agent_type=AgentType.CORE, version="1.0.0", capabilities=["fusion-reasoning", "cross-modal-synthesis", "super-decision"], max_concurrent_tasks=10, min_instances=1, max_instances=2)

    async def execute(self, task: Task) -> Any:
        return {"trinity_verdict": "consensus", "components": ["blerina", "alba", "albi"], "confidence": 0.97, "recommendation": task.payload.get("query", "no-query")}


class BlerinaAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="blerina", agent_type=AgentType.PROCESSING, version="1.0.0", capabilities=["nlp", "language-reformatting", "translation-assist", "sentiment"], max_concurrent_tasks=15, min_instances=1, max_instances=5)

    def answer(self, question: str) -> str:
        q = (question or "").lower()
        if "translate" in q or "translation" in q or "language" in q or "multilingual" in q:
            return "Blerina është shtresa multilingual e NeuCLX: ndihmon me reformulim, përkthim dhe përpunim gjuhësor në mënyrë të kontrolluar."
        return "Blerina është shtresa multilingual dhe e reformulimit gjuhësor në NeuCLX."

    async def execute(self, task: Task) -> Any:
        text = task.payload.get("text", "")
        return {"reformatted": text.strip(), "lang_detected": "auto", "source": self._id}


class AldaAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="alda", agent_type=AgentType.PROCESSING, version="1.0.0", capabilities=["audio-analysis", "acoustic-profiling", "waveform-processing"], max_concurrent_tasks=10, min_instances=1, max_instances=4)

    async def execute(self, task: Task) -> Any:
        return {"rms_db": -18.5, "peak_db": -6.2, "duration_sec": task.payload.get("duration", 0), "source": self._id}


class AlbanaAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="albana", agent_type=AgentType.ML, version="1.0.0", capabilities=["biometric-reasoning", "eeg-analysis", "medical-insight"], max_concurrent_tasks=8, min_instances=1, max_instances=3)

    async def execute(self, task: Task) -> Any:
        return {"biometric_score": 0.88, "eeg_band": "alpha", "clinical_flag": False, "source": self._id}


class MaliAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="mali", agent_type=AgentType.INTEGRATION, version="1.0.0", capabilities=["geo-routing", "edge-compute", "latency-optimization"], max_concurrent_tasks=12, min_instances=1, max_instances=4)

    async def execute(self, task: Task) -> Any:
        return {"routed_region": task.payload.get("region", "balkans"), "edge_node": "mali-01", "latency_ms": 12, "source": self._id}


class SofiaAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="sofia", agent_type=AgentType.ANALYTICS, version="1.0.0", capabilities=["chemistry-analysis", "lab-automation", "research-synthesis"], max_concurrent_tasks=8, min_instances=1, max_instances=3)

    async def execute(self, task: Task) -> Any:
        return {"compound": task.payload.get("compound", "unknown"), "purity": 0.999, "lab": "sofia-chemistry", "source": self._id}


class LiamAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="liam", agent_type=AgentType.INTEGRATION, version="1.0.0", capabilities=["sdk-bridge", "developer-tools", "code-gen"], max_concurrent_tasks=15, min_instances=1, max_instances=5)

    async def execute(self, task: Task) -> Any:
        return {"bridged": True, "sdk": task.payload.get("sdk", "python"), "version": "latest", "source": self._id}


class KlajdiAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="klajdi", agent_type=AgentType.INTEGRATION, version="1.0.0", capabilities=["security-audit", "access-control", "compliance-check"], max_concurrent_tasks=10, min_instances=1, max_instances=3)

    async def execute(self, task: Task) -> Any:
        return {"passed": True, "findings": [], "severity": "none", "source": self._id}


class EAPAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="eap", agent_type=AgentType.PROCESSING, version="1.0.0", capabilities=["workflow-automation", "process-orchestration", "enterprise-integration"], max_concurrent_tasks=20, min_instances=1, max_instances=6)

    async def execute(self, task: Task) -> Any:
        return {"workflow": task.payload.get("workflow", "default"), "triggered": True, "steps_queued": 3, "source": self._id}


class MatiaAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="matia", agent_type=AgentType.ANALYTICS, version="1.0.0", capabilities=["marketplace-analysis", "product-matching", "pricing-intelligence"], max_concurrent_tasks=15, min_instances=1, max_instances=5)

    async def execute(self, task: Task) -> Any:
        return {"matches": [], "query": task.payload.get("query", ""), "marketplace": "clisonix", "source": self._id}


class VideoCreatorAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="video-creator", agent_type=AgentType.ML, version="1.0.0", capabilities=["video-generation", "scene-rendering", "subtitle-generation"], max_concurrent_tasks=4, min_instances=1, max_instances=3)

    async def execute(self, task: Task) -> Any:
        return {"job_id": f"vid_{uuid.uuid4().hex[:8]}", "prompt": task.payload.get("prompt", ""), "status": "queued", "source": self._id}


class NewsPublisherAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="news-publisher", agent_type=AgentType.PROCESSING, version="1.0.0", capabilities=["news-generation", "content-publishing", "rss-feed"], max_concurrent_tasks=10, min_instances=1, max_instances=4)

    async def execute(self, task: Task) -> Any:
        return {"article_id": f"news_{uuid.uuid4().hex[:8]}", "topic": task.payload.get("topic", ""), "published": False, "status": "draft", "source": self._id}


class SelflearningAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="selflearning", agent_type=AgentType.ML, version="1.0.0", capabilities=["reinforcement-learning", "feedback-processing", "memory-consolidation"], max_concurrent_tasks=5, min_instances=1, max_instances=2)

    async def execute(self, task: Task) -> Any:
        return {"signal_absorbed": True, "signal": task.payload.get("signal", "success"), "memory_updated": True, "source": self._id}


class NanogridAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="nanogrid", agent_type=AgentType.ANALYTICS, version="1.0.0", capabilities=["energy-monitoring", "nanodecibel-metrics", "compute-grid"], max_concurrent_tasks=12, min_instances=1, max_instances=4)

    async def execute(self, task: Task) -> Any:
        return {"power_w": 0.0, "nanodecibel_ndb": 0.0, "grid_nodes": 0, "status": "nominal", "source": self._id}


class ZeissAgent(BaseAgent):
    @property
    def config(self) -> AgentConfig:
        return AgentConfig(name="zeiss", agent_type=AgentType.ML, version="1.0.0", capabilities=["optical-analysis", "image-calibration", "microscopy"], max_concurrent_tasks=8, min_instances=1, max_instances=3)

    async def execute(self, task: Task) -> Any:
        return {"sharpness_score": 0.0, "aberration": "none", "magnification": task.payload.get("magnification", 1), "source": self._id}


class AgentPool:
    def __init__(self, agent_factory: Callable[[], BaseAgent], min_instances: int = 1, max_instances: int = 5):
        self._factory = agent_factory
        self._min_instances = min_instances
        self._max_instances = max_instances
        self._agents: List[BaseAgent] = []
        self._lock = threading.Lock()
        self._task_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._workers: List[asyncio.Task] = []

    @property
    def size(self) -> int:
        return len(self._agents)

    @property
    def available_agents(self) -> List[BaseAgent]:
        return [a for a in self._agents if a.can_accept_task()]

    @property
    def pool_metrics(self) -> Dict[str, Any]:
        return {
            "total_instances": len(self._agents),
            "available": len(self.available_agents),
            "busy": len([a for a in self._agents if a.status == AgentStatus.BUSY]),
            "queue_size": self._task_queue.qsize(),
            "min_instances": self._min_instances,
            "max_instances": self._max_instances,
        }

    async def initialize(self):
        for _ in range(self._min_instances):
            await self._add_instance()
        self._running = True
        logger.info(f"✅ Pool initialized with {self._min_instances} instances")

    async def shutdown(self):
        self._running = False
        for worker in self._workers:
            worker.cancel()
        for agent in self._agents:
            await agent.shutdown()
        self._agents.clear()
        logger.info("🛑 Pool shutdown complete")

    async def _add_instance(self) -> Optional[BaseAgent]:
        if len(self._agents) >= self._max_instances:
            return None
        with self._lock:
            agent = self._factory()
            asyncio.get_running_loop().create_task(agent.initialize())
            self._agents.append(agent)
            logger.info(f"📈 Added instance: {agent.id} (total: {len(self._agents)})")
            return agent

    async def _remove_instance(self) -> bool:
        if len(self._agents) <= self._min_instances:
            return False
        with self._lock:
            for agent in self._agents:
                if agent.status == AgentStatus.READY:
                    await agent.shutdown()
                    self._agents.remove(agent)
                    logger.info(f"📉 Removed instance: {agent.id} (total: {len(self._agents)})")
                    return True
        return False

    def get_best_agent(self, task: Task) -> Optional[BaseAgent]:
        available = self.available_agents
        if not available:
            return None
        available.sort(key=lambda a: a.metrics.current_load)
        return available[0]

    async def submit(self, task: Task) -> TaskResult:
        agent = self.get_best_agent(task)
        if not agent:
            agent = await self._add_instance()
            if not agent:
                return TaskResult(task_id=task.task_id, agent_id="pool", success=False, error="No available agents, pool at maximum capacity")
        return await agent._run_task(task)

    async def scale(self, target: int) -> Dict[str, Any]:
        target = max(self._min_instances, min(self._max_instances, target))
        current = len(self._agents)
        if target > current:
            for _ in range(target - current):
                await self._add_instance()
        elif target < current:
            for _ in range(current - target):
                await self._remove_instance()
        return {"previous": current, "current": len(self._agents), "target": target}


class AgentRegistry:
    def __init__(self):
        self._pools: Dict[str, AgentPool] = {}
        self._agent_configs: Dict[str, AgentConfig] = {}
        self._lock = threading.Lock()

    def register(self, agent_class: type, min_instances: int = 1, max_instances: int = 5) -> str:
        temp_agent = agent_class()
        config = temp_agent.config
        name = normalize_agent_identifier(config.name)
        if name in self._pools:
            logger.warning(f"Agent {name} already registered, skipping")
            return name
        pool = AgentPool(agent_factory=agent_class, min_instances=min_instances, max_instances=max_instances)
        with self._lock:
            self._pools[name] = pool
            self._agent_configs[name] = config
        logger.info(f"✅ Registered agent: {name} ({config.agent_type.value})")
        return name

    def unregister(self, name: str) -> bool:
        name = normalize_agent_identifier(name)
        if name not in self._pools:
            return False
        with self._lock:
            del self._pools[name]
            del self._agent_configs[name]
        logger.info(f"🗑️ Unregistered agent: {name}")
        return True

    def get_pool(self, name: str) -> Optional[AgentPool]:
        return self._pools.get(normalize_agent_identifier(name))

    def get_config(self, name: str) -> Optional[AgentConfig]:
        return self._agent_configs.get(normalize_agent_identifier(name))

    def find_by_capability(self, capability: str) -> List[str]:
        matching = []
        for name, config in self._agent_configs.items():
            if capability in config.capabilities:
                matching.append(name)
        return matching

    def list_agents(self) -> List[Dict[str, Any]]:
        result = []
        for name, config in self._agent_configs.items():
            pool = self._pools.get(name)
            result.append({"name": name, "config": config.to_dict(), "pool": pool.pool_metrics if pool else None})
        return result

    async def initialize_all(self):
        for _, pool in self._pools.items():
            await pool.initialize()
        logger.info(f"✅ Initialized {len(self._pools)} agent pools")

    async def shutdown_all(self):
        for pool in self._pools.values():
            await pool.shutdown()
        logger.info("🛑 All agent pools shutdown")


class AgentOrchestrator:
    def __init__(self, auto_register_core: bool = True):
        self._registry = AgentRegistry()
        self._start_time = time.time()
        self._task_counter = 0
        self._lock = threading.Lock()
        if auto_register_core:
            self._register_core_agents()

    def _register_core_agents(self):
        self._registry.register(ALBAAgent, min_instances=1, max_instances=5)
        self._registry.register(ALBIAgent, min_instances=1, max_instances=8)
        self._registry.register(JONAAgent, min_instances=1, max_instances=3)
        self._registry.register(ASIAgent, min_instances=1, max_instances=3)
        self._registry.register(ASITrinityAgent, min_instances=1, max_instances=2)
        self._registry.register(BlerinaAgent, min_instances=1, max_instances=5)
        self._registry.register(AldaAgent, min_instances=1, max_instances=4)
        self._registry.register(AlbanaAgent, min_instances=1, max_instances=3)
        self._registry.register(MaliAgent, min_instances=1, max_instances=4)
        self._registry.register(SofiaAgent, min_instances=1, max_instances=3)
        self._registry.register(LiamAgent, min_instances=1, max_instances=5)
        self._registry.register(KlajdiAgent, min_instances=1, max_instances=3)
        self._registry.register(EAPAgent, min_instances=1, max_instances=6)
        self._registry.register(MatiaAgent, min_instances=1, max_instances=5)
        self._registry.register(VideoCreatorAgent, min_instances=1, max_instances=3)
        self._registry.register(NewsPublisherAgent, min_instances=1, max_instances=4)
        self._registry.register(SelflearningAgent, min_instances=1, max_instances=2)
        self._registry.register(NanogridAgent, min_instances=1, max_instances=4)
        self._registry.register(ZeissAgent, min_instances=1, max_instances=3)

    async def initialize(self):
        await self._registry.initialize_all()
        logger.info("🚀 Agent Orchestrator initialized")

    async def shutdown(self):
        await self._registry.shutdown_all()
        logger.info("🛑 Agent Orchestrator shutdown")

    def register(self, agent_class: type, min_instances: int = 1, max_instances: int = 5) -> str:
        return self._registry.register(agent_class, min_instances, max_instances)

    async def submit(self, agent_name: str, payload: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL, timeout: float = 30.0) -> TaskResult:
        normalized_name = normalize_agent_identifier(agent_name)
        pool = self._registry.get_pool(normalized_name)
        if not pool:
            return TaskResult(task_id="unknown", agent_id="orchestrator", success=False, error=f"Agent '{agent_name}' not found")
        with self._lock:
            self._task_counter += 1
            task_id = f"task_{self._task_counter}_{uuid.uuid4().hex[:6]}"
        task = Task(task_id=task_id, agent_name=normalized_name, payload=payload, priority=priority, timeout=timeout)
        return await pool.submit(task)

    async def submit_by_capability(self, capability: str, payload: Dict[str, Any], priority: TaskPriority = TaskPriority.NORMAL) -> TaskResult:
        agents = self._registry.find_by_capability(capability)
        if not agents:
            return TaskResult(task_id="unknown", agent_id="orchestrator", success=False, error=f"No agent found with capability '{capability}'")
        return await self.submit(agents[0], payload, priority)

    async def broadcast(self, payload: Dict[str, Any], agent_names: Optional[List[str]] = None) -> Dict[str, TaskResult]:
        if agent_names is None:
            agent_names = ["alba", "albi", "jona"]
        results: Dict[str, TaskResult] = {}
        tasks: List[Awaitable[TaskResult]] = [self.submit(name, payload) for name in agent_names]
        task_results = await asyncio.gather(*tasks, return_exceptions=True)
        for name, result in zip(agent_names, task_results):
            if isinstance(result, Exception):
                results[name] = TaskResult(task_id="unknown", agent_id=name, success=False, error=str(result))
            elif isinstance(result, TaskResult):
                results[name] = result
            else:
                results[name] = TaskResult(task_id="unknown", agent_id=name, success=False, error="unexpected_broadcast_result_type")
        return results

    async def scale(self, agent_name: str, target: int) -> Dict[str, Any]:
        normalized_name = normalize_agent_identifier(agent_name)
        pool = self._registry.get_pool(normalized_name)
        if not pool:
            return {"error": f"Agent '{agent_name}' not found"}
        return await pool.scale(target)

    def list_agents(self) -> List[Dict[str, Any]]:
        return self._registry.list_agents()

    def find_agents(self, capability: str) -> List[str]:
        return self._registry.find_by_capability(capability)

    @property
    def status(self) -> Dict[str, Any]:
        agents = self._registry.list_agents()
        total_instances = sum(a["pool"]["total_instances"] for a in agents if a["pool"])
        available = sum(a["pool"]["available"] for a in agents if a["pool"])
        return {"status": "operational", "uptime_seconds": time.time() - self._start_time, "total_tasks_processed": self._task_counter, "agents": {"registered": len(agents), "total_instances": total_instances, "available_instances": available}, "timestamp": datetime.now(timezone.utc).isoformat()}


_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator


async def init_agents() -> AgentOrchestrator:
    orchestrator = get_orchestrator()
    await orchestrator.initialize()
    return orchestrator


async def shutdown_agents():
    global _orchestrator
    if _orchestrator:
        await _orchestrator.shutdown()
        _orchestrator = None


async def demo():
    print("\n" + "=" * 70)
    print("🤖 CLISONIX UNIFIED AGENTS SYSTEM - DEMO")
    print("=" * 70 + "\n")
    orchestrator = AgentOrchestrator()
    await orchestrator.initialize()
    print("\n📋 Registered Agents:")
    for agent in orchestrator.list_agents():
        print(f"  • {agent['name']} ({agent['config']['agent_type']}) - {agent['pool']['total_instances']} instances")
    print("\n🔍 Agents with 'pattern-recognition' capability:")
    print(f"  {orchestrator.find_agents('pattern-recognition')}")
    print("\n📨 Submitting tasks...")
    result = await orchestrator.submit("alba", {"action": "collect"})
    print(f"  ALBA result: success={result.success}, duration={result.duration_ms:.2f}ms")
    result = await orchestrator.submit("albi", {"action": "detect_anomaly"})
    print(f"  ALBI result: success={result.success}, duration={result.duration_ms:.2f}ms")
    result = await orchestrator.submit("jona", {"action": "recommend"})
    print(f"  JONA result: success={result.success}, duration={result.duration_ms:.2f}ms")
    print("\n📡 Broadcasting to all core agents...")
    results = await orchestrator.broadcast({"action": "health_check"})
    for name, result in results.items():
        print(f"  {name.upper()}: success={result.success}")
    print("\n📈 Scaling ALBA to 3 instances...")
    scale_result = await orchestrator.scale("alba", 3)
    print(f"  Scale result: {scale_result}")
    print("\n📊 Orchestrator Status:")
    status = orchestrator.status
    print(f"  Total tasks: {status['total_tasks_processed']}")
    print(f"  Total instances: {status['agents']['total_instances']}")
    print(f"  Available: {status['agents']['available_instances']}")
    await orchestrator.shutdown()
    print("\n✅ Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo())


__all__ = [
    "AgentAnswer",
    "AgentConfig",
    "AgentMetrics",
    "AgentOrchestrator",
    "AgentPool",
    "AgentRegistry",
    "AgentStatus",
    "AgentType",
    "ALBAAgent",
    "ALBIAgent",
    "AldaAgent",
    "AlbanaAgent",
    "AlbaAgent",
    "AlbiAgent",
    "ASIAgent",
    "ASITrinityAgent",
    "BaseAgent",
    "BlerinaAgent",
    "EAPAgent",
    "JONAAgent",
    "JonaAgent",
    "KlajdiAgent",
    "LiamAgent",
    "LoadBalanceStrategy",
    "MaliAgent",
    "MatiaAgent",
    "NanogridAgent",
    "NewsPublisherAgent",
    "SelflearningAgent",
    "SofiaAgent",
    "Task",
    "TaskPriority",
    "TaskResult",
    "VideoCreatorAgent",
    "ZeissAgent",
    "get_orchestrator",
    "init_agents",
    "normalize_agent_identifier",
    "shutdown_agents",
]
