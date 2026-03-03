#!/usr/bin/env python3
"""
CyberDog RL Training Environment
Gym-compatible environment for reinforcement learning with Gazebo simulation
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from rclpy.callback_groups import ReentrantCallbackGroup
from std_msgs.msg import Float64MultiArray, Bool
from sensor_msgs.msg import JointState, Imu
from geometry_msgs.msg import Twist, Pose
from nav_msgs.msg import Odometry
from gazebo_msgs.srv import SetEntityState, GetEntityState
import numpy as np
from typing import Optional, Tuple, Dict, Any
import time
import gym
from gym import spaces


class CyberDogEnv(Node, gym.Env):
    """
    CyberDog reinforcement learning environment.
    
    Combines ROS2 node functionality with OpenAI Gym interface.
    Compatible with Stable Baselines3, RLlib, and other RL libraries.
    
    Observation Space (37 dimensions):
        - Joint positions (12): 12 joint angles
        - Joint velocities (12): 12 joint angular velocities
        - Base orientation (4): quaternion (x, y, z, w)
        - Base angular velocity (3): IMU gyroscope
        - Base linear velocity (3): odometry velocity
        - Target velocity (3): desired x, y, yaw velocity
    
    Action Space (12 dimensions):
        - Joint position targets for 12 joints
    
    Reward:
        - Forward velocity reward + stability penalty + energy penalty
    """
    
    metadata = {'render.modes': ['human']}
    
    # Joint names in order
    JOINT_NAMES = [
        'front_left_hip', 'front_left_thigh', 'front_left_calf',
        'front_right_hip', 'front_right_thigh', 'front_right_calf',
        'rear_left_hip', 'rear_left_thigh', 'rear_left_calf',
        'rear_right_hip', 'rear_right_thigh', 'rear_right_calf',
    ]
    
    # Default joint positions (standing)
    DEFAULT_JOINT_POSITIONS = np.array([
        0.0, 0.6, -1.2,  # Front left
        0.0, 0.6, -1.2,  # Front right
        0.0, 0.6, -1.2,  # Rear left
        0.0, 0.6, -1.2,  # Rear right
    ])
    
    def __init__(
        self,
        namespace: str = '/cyberdog',
        robot_name: str = 'cyberdog',
        target_velocity: float = 0.5,
        max_episode_steps: int = 1000,
        reset_delay: float = 0.5,
    ):
        # Initialize ROS2 node
        Node.__init__(self, 'cyberdog_rl_env')
        gym.Env.__init__(self)
        
        self.namespace = namespace
        self.robot_name = robot_name
        self.target_velocity = target_velocity
        self.max_episode_steps = max_episode_steps
        self.reset_delay = reset_delay
        
        # State variables
        self.joint_positions = np.zeros(12)
        self.joint_velocities = np.zeros(12)
        self.base_orientation = np.array([0, 0, 0, 1])  # quaternion
        self.base_angular_velocity = np.zeros(3)
        self.base_linear_velocity = np.zeros(3)
        self.base_position = np.zeros(3)
        
        # Episode tracking
        self.current_step = 0
        self.done = False
        
        # Define action and observation spaces
        self.action_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(12,),
            dtype=np.float32
        )
        
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(37,),
            dtype=np.float32
        )
        
        # Callback group for concurrent callbacks
        self.callback_group = ReentrantCallbackGroup()
        
        # Publishers
        self.joint_cmd_pub = self.create_publisher(
            Float64MultiArray,
            f'{namespace}/joint_group_position_controller/commands',
            10
        )
        
        self.cmd_vel_pub = self.create_publisher(
            Twist,
            f'{namespace}/cmd_vel',
            10
        )
        
        # Subscribers
        self.joint_state_sub = self.create_subscription(
            JointState,
            f'{namespace}/joint_states',
            self._joint_state_callback,
            10,
            callback_group=self.callback_group
        )
        
        self.imu_sub = self.create_subscription(
            Imu,
            f'{namespace}/imu/data',
            self._imu_callback,
            10,
            callback_group=self.callback_group
        )
        
        self.odom_sub = self.create_subscription(
            Odometry,
            f'{namespace}/odom',
            self._odom_callback,
            10,
            callback_group=self.callback_group
        )
        
        # Gazebo service clients for reset
        self.set_entity_state_client = self.create_client(
            SetEntityState,
            '/gazebo/set_entity_state'
        )
        
        self.get_entity_state_client = self.create_client(
            GetEntityState,
            '/gazebo/get_entity_state'
        )
        
        self.get_logger().info('CyberDog RL Environment initialized')
    
    def _joint_state_callback(self, msg: JointState):
        """Update joint states from /joint_states topic."""
        for i, name in enumerate(self.JOINT_NAMES):
            try:
                idx = msg.name.index(name)
                self.joint_positions[i] = msg.position[idx]
                self.joint_velocities[i] = msg.velocity[idx]
            except ValueError:
                pass
    
    def _imu_callback(self, msg: Imu):
        """Update IMU data from /imu/data topic."""
        self.base_orientation = np.array([
            msg.orientation.x,
            msg.orientation.y,
            msg.orientation.z,
            msg.orientation.w,
        ])
        self.base_angular_velocity = np.array([
            msg.angular_velocity.x,
            msg.angular_velocity.y,
            msg.angular_velocity.z,
        ])
    
    def _odom_callback(self, msg: Odometry):
        """Update odometry from /odom topic."""
        self.base_position = np.array([
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.pose.pose.position.z,
        ])
        self.base_linear_velocity = np.array([
            msg.twist.twist.linear.x,
            msg.twist.twist.linear.y,
            msg.twist.twist.linear.z,
        ])
    
    def get_observation(self) -> np.ndarray:
        """
        Get current observation.
        
        Returns:
            np.ndarray: Observation vector (37 dimensions)
        """
        target_vel = np.array([self.target_velocity, 0.0, 0.0])
        
        obs = np.concatenate([
            self.joint_positions,
            self.joint_velocities,
            self.base_orientation,
            self.base_angular_velocity,
            self.base_linear_velocity,
            target_vel,
        ]).astype(np.float32)
        
        return obs
    
    def compute_reward(self) -> float:
        """
        Compute reward for current state.
        
        Reward components:
            - Forward velocity reward: Encourages forward movement
            - Stability reward: Penalizes large roll/pitch
            - Energy penalty: Penalizes large joint velocities
            - Alive reward: Small bonus for staying upright
        
        Returns:
            float: Total reward
        """
        # Forward velocity reward
        forward_vel = self.base_linear_velocity[0]
        vel_reward = 2.0 * forward_vel
        
        # Stability reward (penalize roll and pitch)
        roll, pitch = self._quat_to_rpy(self.base_orientation)[:2]
        stability_penalty = -0.5 * (abs(roll) + abs(pitch))
        
        # Energy penalty
        energy_penalty = -0.001 * np.sum(np.abs(self.joint_velocities))
        
        # Height penalty (fall detection)
        if self.base_position[2] < 0.15:
            height_penalty = -10.0
            self.done = True
        else:
            height_penalty = 0.0
        
        # Alive reward
        alive_reward = 0.1
        
        total_reward = vel_reward + stability_penalty + energy_penalty + height_penalty + alive_reward
        return float(total_reward)
    
    def _quat_to_rpy(self, quat: np.ndarray) -> np.ndarray:
        """Convert quaternion to roll, pitch, yaw."""
        x, y, z, w = quat
        
        # Roll (x-axis rotation)
        sinr_cosp = 2 * (w * x + y * z)
        cosr_cosp = 1 - 2 * (x * x + y * y)
        roll = np.arctan2(sinr_cosp, cosr_cosp)
        
        # Pitch (y-axis rotation)
        sinp = 2 * (w * y - z * x)
        pitch = np.arcsin(np.clip(sinp, -1.0, 1.0))
        
        # Yaw (z-axis rotation)
        siny_cosp = 2 * (w * z + x * y)
        cosy_cosp = 1 - 2 * (y * y + z * z)
        yaw = np.arctan2(siny_cosp, cosy_cosp)
        
        return np.array([roll, pitch, yaw])
    
    def step(self, action: np.ndarray) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        """
        Execute one environment step.
        
        Args:
            action: Joint position commands (normalized to [-1, 1])
        
        Returns:
            observation, reward, done, info
        """
        # Scale action from [-1, 1] to joint limits
        joint_targets = self.DEFAULT_JOINT_POSITIONS + 0.5 * action
        
        # Publish joint commands
        cmd_msg = Float64MultiArray()
        cmd_msg.data = joint_targets.tolist()
        self.joint_cmd_pub.publish(cmd_msg)
        
        # Spin once to process callbacks
        rclpy.spin_once(self, timeout_sec=0.01)
        
        # Compute reward
        reward = self.compute_reward()
        
        # Check termination
        self.current_step += 1
        if self.current_step >= self.max_episode_steps:
            self.done = True
        
        # Get observation
        observation = self.get_observation()
        
        info = {
            'x_position': self.base_position[0],
            'y_position': self.base_position[1],
            'forward_velocity': self.base_linear_velocity[0],
            'episode_step': self.current_step,
        }
        
        return observation, reward, self.done, info
    
    def reset(self) -> np.ndarray:
        """
        Reset environment to initial state.
        
        Returns:
            Initial observation
        """
        self.current_step = 0
        self.done = False
        
        # Reset robot in Gazebo
        self._reset_robot()
        
        # Reset state variables
        self.joint_positions = self.DEFAULT_JOINT_POSITIONS.copy()
        self.joint_velocities = np.zeros(12)
        self.base_orientation = np.array([0, 0, 0, 1])
        self.base_angular_velocity = np.zeros(3)
        self.base_linear_velocity = np.zeros(3)
        self.base_position = np.array([0, 0, 0.3])
        
        # Spin to receive initial messages
        for _ in range(10):
            rclpy.spin_once(self, timeout_sec=0.1)
        
        time.sleep(self.reset_delay)
        
        return self.get_observation()
    
    def _reset_robot(self):
        """Reset robot pose in Gazebo."""
        if not self.set_entity_state_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('SetEntityState service not available')
            return
        
        request = SetEntityState.Request()
        request.state.name = self.robot_name
        request.state.pose.position.x = 0.0
        request.state.pose.position.y = 0.0
        request.state.pose.position.z = 0.3
        request.state.pose.orientation.w = 1.0
        request.state.twist.linear.x = 0.0
        request.state.twist.linear.y = 0.0
        request.state.twist.linear.z = 0.0
        request.state.twist.angular.x = 0.0
        request.state.twist.angular.y = 0.0
        request.state.twist.angular.z = 0.0
        
        future = self.set_entity_state_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
    
    def render(self, mode='human'):
        """Render environment (Gazebo provides visualization)."""
        pass
    
    def close(self):
        """Clean up resources."""
        self.destroy_node()


class CyberDogEnvWrapper(gym.Env):
    """
    Standalone wrapper that handles ROS2 initialization.
    Use this with Stable Baselines3.
    """
    
    def __init__(self, **kwargs):
        # Initialize ROS2 if not already done
        if not rclpy.ok():
            rclpy.init()
        
        self.env = CyberDogEnv(**kwargs)
        self.action_space = self.env.action_space
        self.observation_space = self.env.observation_space
    
    def step(self, action):
        return self.env.step(action)
    
    def reset(self):
        return self.env.reset()
    
    def render(self, mode='human'):
        return self.env.render(mode)
    
    def close(self):
        self.env.close()


# Convenience function for SB3
def make_cyberdog_env(**kwargs):
    """Create CyberDog environment for use with Stable Baselines3."""
    return CyberDogEnvWrapper(**kwargs)


if __name__ == '__main__':
    # Test the environment
    rclpy.init()
    
    env = CyberDogEnv()
    obs = env.reset()
    
    print(f'Initial observation shape: {obs.shape}')
    print(f'Initial observation: {obs}')
    
    for i in range(10):
        action = env.action_space.sample()
        obs, reward, done, info = env.step(action)
        print(f'Step {i}: reward={reward:.3f}, done={done}')
        
        if done:
            break
    
    env.close()
    rclpy.shutdown()
