"""
Basic tests for configuration module
"""

import pytest
from pathlib import Path
from src.config import Config


def test_config_from_env(monkeypatch):
    """Test loading config from environment variables"""
    monkeypatch.setenv('TC_EMAIL', 'test@example.com')
    monkeypatch.setenv('TC_PASSWORD', 'testpass')
    monkeypatch.setenv('SCHOOL', '12345')
    monkeypatch.setenv('CHILD', '67890')
    monkeypatch.setenv('SCHOOL_LAT', '41.9032')
    monkeypatch.setenv('SCHOOL_LNG', '-87.6663')
    monkeypatch.setenv('SCHOOL_KEYWORDS', 'test')

    config = Config.from_env()

    assert config.email == 'test@example.com'
    assert config.password == 'testpass'
    assert config.school_id == 12345
    assert config.child_id == 67890
    assert config.school_lat == 41.9032
    assert config.school_lng == -87.6663
    assert config.school_keywords == 'test'


def test_config_validation():
    """Test config validation"""
    # Valid config
    config = Config(
        email='test@example.com',
        password='testpass',
        school_id=12345,
        child_id=67890,
        school_lat=0.0,
        school_lng=0.0,
        school_keywords=''
    )
    assert config.validate() is True

    # Invalid config (missing email)
    config = Config(
        email='',
        password='testpass',
        school_id=12345,
        child_id=67890,
        school_lat=0.0,
        school_lng=0.0,
        school_keywords=''
    )
    assert config.validate() is False

    # Invalid config (missing school_id)
    config = Config(
        email='test@example.com',
        password='testpass',
        school_id=0,
        child_id=67890,
        school_lat=0.0,
        school_lng=0.0,
        school_keywords=''
    )
    assert config.validate() is False


def test_config_get_file_path():
    """Test getting config file path"""
    path = Config.get_config_file_path()
    assert isinstance(path, Path)
    assert path.name == 'config.yaml'
    assert 'transparent-classroom-photos-grabber' in str(path)
