from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class ViralSignal:
    """Viral detection signal"""
    video_id: str

    # Scores
    growth_score: float = 0.0
    growth_stage: str = "unknown"  # 'normal', 'takeoff', 'explosion'

    # Benchmark
    vs_benchmark: Dict[str, Any] = field(default_factory=dict)

    # Decision
    should_alert: bool = False
    alert_level: str = "none"  # 'none', 'yellow', 'orange', 'red'
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "video_id": self.video_id,
            "growth_score": self.growth_score,
            "growth_stage": self.growth_stage,
            "vs_benchmark": self.vs_benchmark,
            "should_alert": self.should_alert,
            "alert_level": self.alert_level,
            "message": self.message
        }
