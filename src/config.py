"""
Configuration management for Transparent Classroom API
Loads settings from environment variables or config file
"""

import os
import yaml
from typing import Optional
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Config:
    """Configuration for Transparent Classroom API"""
    email: str
    password: str
    school_id: int
    child_id: int
    school_lat: float
    school_lng: float
    school_keywords: str
    output_dir: str = "./photos"
    cache_dir: str = "./cache"
    cache_timeout: int = 14400  # 4 hours in seconds
    cron_expression: Optional[str] = None  # Optional cron expression for scheduling

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        return cls(
            email=os.getenv('TC_EMAIL', ''),
            password=os.getenv('TC_PASSWORD', ''),
            school_id=int(os.getenv('SCHOOL', 0)),
            child_id=int(os.getenv('CHILD', 0)),
            school_lat=float(os.getenv('SCHOOL_LAT', 0.0)),
            school_lng=float(os.getenv('SCHOOL_LNG', 0.0)),
            school_keywords=os.getenv('SCHOOL_KEYWORDS', ''),
            output_dir=os.getenv('OUTPUT_DIR', './photos'),
            cache_dir=os.getenv('CACHE_DIR', './cache'),
            cache_timeout=int(os.getenv('CACHE_TIMEOUT', 14400)),
            cron_expression=os.getenv('CRON_EXPRESSION', None)
        )

    @classmethod
    def from_file(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = cls.get_config_file_path()

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)

        return cls(
            email=data.get('email', ''),
            password=data.get('password', ''),
            school_id=int(data.get('school_id', 0)),
            child_id=int(data.get('child_id', 0)),
            school_lat=float(data.get('school_lat', 0.0)),
            school_lng=float(data.get('school_lng', 0.0)),
            school_keywords=data.get('school_keywords', ''),
            output_dir=data.get('output_dir', './photos'),
            cache_dir=data.get('cache_dir', './cache'),
            cache_timeout=int(data.get('cache_timeout', 14400)),
            cron_expression=data.get('cron_expression', None)
        )

    @staticmethod
    def get_config_file_path() -> Path:
        """Get the standard config file path"""
        config_dir = Path.home() / '.config' / 'transparent-classroom-photos-grabber'
        return config_dir / 'config.yaml'

    @classmethod
    def load(cls) -> "Config":
        """Load configuration from multiple sources in priority order"""
        # Try environment variables first
        try:
            config = cls.from_env()
            if config.email and config.password and config.school_id and config.child_id:
                return config
        except Exception:
            pass

        # Try config file
        try:
            return cls.from_file()
        except Exception:
            pass

        # Fallback to environment variables even if incomplete
        return cls.from_env()

    def save_to_file(self, config_path: Optional[Path] = None):
        """Save configuration to YAML file"""
        if config_path is None:
            config_path = self.get_config_file_path()

        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            'email': self.email,
            'password': self.password,
            'school_id': self.school_id,
            'child_id': self.child_id,
            'school_lat': self.school_lat,
            'school_lng': self.school_lng,
            'school_keywords': self.school_keywords,
            'output_dir': self.output_dir,
            'cache_dir': self.cache_dir,
            'cache_timeout': self.cache_timeout
        }

        with open(config_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)

    def validate(self) -> bool:
        """Validate that required configuration is present"""
        return all([
            self.email,
            self.password,
            self.school_id > 0,
            self.child_id > 0
        ])
