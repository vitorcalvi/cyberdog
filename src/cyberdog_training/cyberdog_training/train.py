#!/usr/bin/env python3
"""
CyberDog Reinforcement Learning Training Script

Train locomotion policies using Stable Baselines3.
Supports PPO, SAC, and TD3 algorithms.

Usage:
    python3 -m cyberdog_training.train --algorithm ppo --timesteps 1000000
    python3 -m cyberdog_training.train --algorithm sac --timesteps 500000
    python3 -m cyberdog_training.train --algorithm ppo --load models/ppo_cyberdog.zip --eval

Prerequisites:
    1. Start Gazebo simulation:
       ros2 launch cyberdog_gazebo gazebo.launch.py
    
    2. Start controllers:
       ros2 control load_controller --set-state start joint_group_position_controller
    
    3. Run this training script
"""

import argparse
import os
from datetime import datetime
from typing import Optional

import numpy as np

# ROS2 imports
import rclpy
from rclpy.executors import MultiThreadedExecutor

# PyTorch import
try:
    import torch
    import torch.nn as nn
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("Warning: PyTorch not installed. Install with:")
    print("  pip install torch")

# Stable Baselines3 imports
try:
    from stable_baselines3 import PPO, SAC, TD3
    from stable_baselines3.common.callbacks import (
        EvalCallback,
        CheckpointCallback,
        CallbackList,
    )
    from stable_baselines3.common.env_util import make_vec_env
    from stable_baselines3.common.vec_env import SubprocVecEnv, DummyVecEnv
    from stable_baselines3.common.monitor import Monitor
    SB3_AVAILABLE = True
except ImportError:
    SB3_AVAILABLE = False
    print("Warning: stable-baselines3 not installed. Install with:")
    print("  pip install stable-baselines3")

# Local imports
from .env_node import CyberDogEnv, CyberDogEnvWrapper


def create_env(rank: int = 0) -> CyberDogEnvWrapper:
    """
    Create a CyberDog environment instance.
    
    Args:
        rank: Environment rank for multi-process training
    
    Returns:
        CyberDogEnvWrapper instance
    """
    env = CyberDogEnvWrapper(
        namespace='/cyberdog',
        robot_name='cyberdog',
        target_velocity=0.5,
        max_episode_steps=1000,
        reset_delay=0.5,
    )
    env = Monitor(env)
    return env


def train_ppo(
    total_timesteps: int = 1_000_000,
    save_path: str = './models',
    log_path: str = './logs',
    n_envs: int = 1,
    learning_rate: float = 3e-4,
    n_steps: int = 2048,
    batch_size: int = 64,
    n_epochs: int = 10,
    gamma: float = 0.99,
    gae_lambda: float = 0.95,
    clip_range: float = 0.2,
    ent_coef: float = 0.01,
    vf_coef: float = 0.5,
    max_grad_norm: float = 0.5,
    eval_freq: int = 10000,
    n_eval_episodes: int = 5,
    checkpoint_freq: int = 50000,
    load_model: Optional[str] = None,
) -> PPO:
    """
    Train CyberDog locomotion using PPO.
    
    Args:
        total_timesteps: Total training timesteps
        save_path: Path to save models
        log_path: Path for tensorboard logs
        n_envs: Number of parallel environments
        learning_rate: Learning rate
        n_steps: Number of steps per update
        batch_size: Minibatch size
        n_epochs: Number of epochs per update
        gamma: Discount factor
        gae_lambda: GAE lambda parameter
        clip_range: PPO clipping parameter
        ent_coef: Entropy coefficient
        vf_coef: Value function coefficient
        max_grad_norm: Maximum gradient norm
        eval_freq: Evaluation frequency
        n_eval_episodes: Number of evaluation episodes
        checkpoint_freq: Checkpoint save frequency
        load_model: Path to load existing model
    
    Returns:
        Trained PPO model
    """
    if not SB3_AVAILABLE:
        raise ImportError("stable-baselines3 is required for training")
    if not TORCH_AVAILABLE:
        raise ImportError("torch is required for training")
    
    # Create directories
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)
    
    # Create environment(s)
    if n_envs > 1:
        env = SubprocVecEnv([lambda: create_env(i) for i in range(n_envs)])
    else:
        env = DummyVecEnv([lambda: create_env(0)])
    
    # Create evaluation environment
    eval_env = DummyVecEnv([lambda: create_env(0)])
    
    # Policy kwargs
    policy_kwargs = dict(
        net_arch=[512, 256, 128],
        activation_fn=torch.nn.ELU,
    )
    
    # Create or load model
    if load_model and os.path.exists(load_model):
        print(f"Loading model from {load_model}")
        model = PPO.load(load_model, env=env, tensorboard_log=log_path)
    else:
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=learning_rate,
            n_steps=n_steps,
            batch_size=batch_size,
            n_epochs=n_epochs,
            gamma=gamma,
            gae_lambda=gae_lambda,
            clip_range=clip_range,
            ent_coef=ent_coef,
            vf_coef=vf_coef,
            max_grad_norm=max_grad_norm,
            policy_kwargs=policy_kwargs,
            tensorboard_log=log_path,
            verbose=1,
        )
    
    # Callbacks
    callbacks = []
    
    # Evaluation callback
    eval_callback = EvalCallback(
        eval_env,
        best_model_save_path=os.path.join(save_path, 'best'),
        log_path=os.path.join(log_path, 'eval'),
        eval_freq=max(eval_freq // n_envs, 1),
        n_eval_episodes=n_eval_episodes,
        deterministic=True,
        render=False,
    )
    callbacks.append(eval_callback)
    
    # Checkpoint callback
    checkpoint_callback = CheckpointCallback(
        save_freq=checkpoint_freq,
        save_path=os.path.join(save_path, 'checkpoints'),
        name_prefix='cyberdog_ppo',
    )
    callbacks.append(checkpoint_callback)
    
    # Train
    print(f"Starting PPO training for {total_timesteps} timesteps...")
    model.learn(
        total_timesteps=total_timesteps,
        callback=CallbackList(callbacks),
        progress_bar=True,
    )
    
    # Save final model
    final_path = os.path.join(save_path, 'ppo_cyberdog_final.zip')
    model.save(final_path)
    print(f"Model saved to {final_path}")
    
    return model


def train_sac(
    total_timesteps: int = 500_000,
    save_path: str = './models',
    log_path: str = './logs',
    learning_rate: float = 3e-4,
    buffer_size: int = 1000000,
    learning_starts: int = 10000,
    batch_size: int = 256,
    tau: float = 0.005,
    gamma: float = 0.99,
    train_freq: int = 1,
    gradient_steps: int = 1,
    ent_coef: str = 'auto',
    load_model: Optional[str] = None,
) -> SAC:
    """
    Train CyberDog locomotion using SAC.
    
    Args:
        total_timesteps: Total training timesteps
        save_path: Path to save models
        log_path: Path for tensorboard logs
        learning_rate: Learning rate
        buffer_size: Replay buffer size
        learning_starts: Timesteps before learning starts
        batch_size: Minibatch size
        tau: Soft update coefficient
        gamma: Discount factor
        train_freq: Training frequency
        gradient_steps: Gradient steps per training step
        ent_coef: Entropy coefficient ('auto' for automatic tuning)
        load_model: Path to load existing model
    
    Returns:
        Trained SAC model
    """
    if not SB3_AVAILABLE:
        raise ImportError("stable-baselines3 is required for training")
    
    # Create directories
    os.makedirs(save_path, exist_ok=True)
    os.makedirs(log_path, exist_ok=True)
    
    # Create environment
    env = DummyVecEnv([lambda: create_env(0)])
    
    # Create or load model
    if load_model and os.path.exists(load_model):
        print(f"Loading model from {load_model}")
        model = SAC.load(load_model, env=env, tensorboard_log=log_path)
    else:
        model = SAC(
            "MlpPolicy",
            env,
            learning_rate=learning_rate,
            buffer_size=buffer_size,
            learning_starts=learning_starts,
            batch_size=batch_size,
            tau=tau,
            gamma=gamma,
            train_freq=train_freq,
            gradient_steps=gradient_steps,
            ent_coef=ent_coef,
            tensorboard_log=log_path,
            verbose=1,
        )
    
    # Train
    print(f"Starting SAC training for {total_timesteps} timesteps...")
    model.learn(total_timesteps=total_timesteps, progress_bar=True)
    
    # Save final model
    final_path = os.path.join(save_path, 'sac_cyberdog_final.zip')
    model.save(final_path)
    print(f"Model saved to {final_path}")
    
    return model


def evaluate(
    model_path: str,
    n_episodes: int = 10,
    render: bool = False,
) -> dict:
    """
    Evaluate a trained model.
    
    Args:
        model_path: Path to trained model
        n_episodes: Number of evaluation episodes
        render: Whether to render
    
    Returns:
        Dictionary with evaluation statistics
    """
    if not SB3_AVAILABLE:
        raise ImportError("stable-baselines3 is required for evaluation")
    
    env = create_env(0)
    model = PPO.load(model_path, env=env)
    
    rewards = []
    lengths = []
    
    for ep in range(n_episodes):
        obs = env.reset()
        done = False
        total_reward = 0
        steps = 0
        
        while not done:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, done, info = env.step(action)
            total_reward += reward
            steps += 1
            
            if render:
                env.render()
        
        rewards.append(total_reward)
        lengths.append(steps)
        print(f"Episode {ep + 1}: reward={total_reward:.2f}, length={steps}")
    
    stats = {
        'mean_reward': np.mean(rewards),
        'std_reward': np.std(rewards),
        'mean_length': np.mean(lengths),
        'std_length': np.std(lengths),
    }
    
    print(f"\nEvaluation Results:")
    print(f"  Mean reward: {stats['mean_reward']:.2f} +/- {stats['std_reward']:.2f}")
    print(f"  Mean length: {stats['mean_length']:.2f} +/- {stats['std_length']:.2f}")
    
    return stats


def main():
    parser = argparse.ArgumentParser(description='Train CyberDog locomotion policies')
    parser.add_argument(
        '--algorithm', '-a',
        type=str,
        choices=['ppo', 'sac', 'td3'],
        default='ppo',
        help='RL algorithm to use'
    )
    parser.add_argument(
        '--timesteps', '-t',
        type=int,
        default=1_000_000,
        help='Total training timesteps'
    )
    parser.add_argument(
        '--save-path',
        type=str,
        default='./models',
        help='Path to save models'
    )
    parser.add_argument(
        '--log-path',
        type=str,
        default='./logs',
        help='Path for tensorboard logs'
    )
    parser.add_argument(
        '--load',
        type=str,
        default=None,
        help='Path to load existing model for continued training'
    )
    parser.add_argument(
        '--eval',
        action='store_true',
        help='Evaluate mode (requires --load)'
    )
    parser.add_argument(
        '--n-episodes',
        type=int,
        default=10,
        help='Number of episodes for evaluation'
    )
    parser.add_argument(
        '--n-envs',
        type=int,
        default=1,
        help='Number of parallel environments'
    )
    
    args = parser.parse_args()
    
    if args.eval:
        if not args.load:
            print("Error: --load is required for evaluation mode")
            return
        evaluate(args.load, args.n_episodes)
    elif args.algorithm == 'ppo':
        train_ppo(
            total_timesteps=args.timesteps,
            save_path=args.save_path,
            log_path=args.log_path,
            n_envs=args.n_envs,
            load_model=args.load,
        )
    elif args.algorithm == 'sac':
        train_sac(
            total_timesteps=args.timesteps,
            save_path=args.save_path,
            log_path=args.log_path,
            load_model=args.load,
        )
    else:
        print(f"Algorithm {args.algorithm} not yet implemented")


if __name__ == '__main__':
    main()
