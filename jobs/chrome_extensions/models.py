from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, Union


@dataclass
class ChromeExtension:
    """Data class representing a Chrome extension with all available metadata."""
    id: str
    name: str
    display_name: str
    short_description: str
    category: Optional[str]
    icon_link: str

    downloads: Optional[Union[str, int]]
    rating: Optional[float]
    rating_count: Optional[int]

    website: Optional[str]
    good_record: bool
    featured: bool

    create_date: str
    version: str
    host_wide_permissions: bool

    def to_dict(self) -> Dict[str, Any]:
        """Convert extension to dictionary."""
        return asdict(self)

    def __str__(self) -> str:
        """String representation of the extension."""
        return f"{self.name} ({self.id}) - {self.rating}★ ({self.rating_count} reviews)"