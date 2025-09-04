from dataclasses import dataclass, asdict
from typing import Dict, Any


@dataclass
class GitleakRule:
    """Data class representing a Chrome extension with all available metadata."""
    rule_id: str
    name: str
    description: str
    regex: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert extension to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """String representation of the extension."""
        return f"{self.rule_id} ({self.name})"
