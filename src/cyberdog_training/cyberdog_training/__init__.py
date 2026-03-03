"""
CyberDog Reinforcement Learning Training Package

Provides Gym-compatible environment and training scripts for CyberDog
locomotion learning using Stable Baselines3.
"""

from .env_node import CyberDogEnv, CyberDogEnvWrapper, make_cyberdog_env

__all__ = [
    'CyberDogEnv',
    'CyberDogEnvWrapper',
    'make_cyberdog_env',
]
__version__ = '0.1.0'
