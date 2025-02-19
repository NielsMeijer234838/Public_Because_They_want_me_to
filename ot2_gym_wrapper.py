from grpc import Status
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from sim_class import Simulation
import pybullet as p
from stable_baselines3.common.callbacks import BaseCallback

class OT2_wrapper(gym.Env):
    def __init__(self, render=False, max_steps=1000):
        # Calls the constructor off the parent class while being bound to the instance of this wrapper
        super(OT2_wrapper, self).__init__()

        # Overwrites render method but I do not know why, The mentors provided this
        self.render = render 
        self.distance_threshold = 0.01

        # Sets some properties that are used during the training of a model
        self.max_steps = max_steps
        self.goal_position = None

        # Sets a pybullet simulation instance with only 1 agent as multiple are not reported
        self.sim = Simulation(render=render, num_agents=1)

        # Define action and observation space
        # They must be gym.spaces objects
        # self.action_space = spaces.Box(low=np.NINF, high=np.inf, shape=(3, ), dtype=np.float32)

        # Action shape with shape (3,) and each low bound set to -1 and high to 1, This limits the speed of the OT2 robot so it does not speedrun death against wall
        self.action_space = spaces.Box(low=np.array([-1, -1, -1]), high=np.array([1, 1, 1]), shape=(3,), dtype=np.float32)

        # The first 3 float32 are the pipette position or the current robot position, The last 3 float32's are the current goal for the episode both are set to the bounds of -1 to 1
        # as the working envelope ranges are smaller than a single pybullet grid unit
        self.observation_space = spaces.Box(low=np.array([-1, -1, -1, -1, -1, -1]), high=np.array([1, 1, 1, 1, 1, 1]), shape=(6,), dtype=np.float32)

        # keep track of the number of steps
        self.steps = 0

    def reset(self, seed=None):
        """Resets the simulation and generates a new goal location within the bounds of the working envelope.

        Args:
            seed (int, optional): Sets the seed random seed of numpy. Defaults to None.

        Returns:
            Observation, List: Contains the xyz coordinates of the pipette current location and the goal position
        """
        if seed is not None:
            np.random.seed(seed)

        # Minimum and maximum gotten from task 9
        # These make sure that the goal generated are within the working envelope of the OT2
        low_bound = [-0.17, -0.16, 0.16]
        high_bound = [0.24, 0.21, 0.28]

        # Generates a 3 random numbers according to the observation space definition
        self.goal_position = np.random.uniform(low=low_bound, high=high_bound, size=(3,)).astype(np.float32)

        # This resets the simulation so it always has a fresh start
        status = self.sim.reset(num_agents=1)

        # If the simulation has multiple agents the robotID are different and the ID might change between resets, For this reason the keys are gotten
        # We only need the first one because the wrapper is made to only support a single agent per simulation
        robot_id = list(status.keys())[0]

        # Observation is set to the pipette position and goal is appended, This results in a array of (6,) np.float32's
        observation = []
        position = np.array(status[robot_id]['pipette_position'], dtype=np.float32)
        observation = np.concatenate([position, self.goal_position]).astype(np.float32)

        # Everytime the simulation is reset for whatever reason the current amount of used steps need to be reset
        self.steps = 0

        # The Gymnasium expects the observations to be returned and a dictionary with info, We do not provide any info in this fuction so a empty dictionary is returned to avoid errors
        return observation, {}
    
    def update_distance_threshold(self, success_rate):
        """Update the distance threshold based on the success rate."""
        if success_rate > 0.8:  # Reduce threshold if success rate is high
            self.distance_threshold = max(
                self.min_threshold, self.distance_threshold * self.threshold_decay
            )
        elif success_rate < 0.2:  # Increase threshold if success rate is low
            self.distance_threshold *= 1.01  # Make the task easier


    def step(self, action: np.ndarray):
        action = np.clip(action, self.action_space.low, self.action_space.high)  # Validate action
        action = np.append(action, 0)  # Add drop action
        
        try:
            observation_data = self.sim.run([action])
        except Exception as e:
            raise RuntimeError(f"Simulation failed: {e}")

        robot_id = list(observation_data.keys())[0]
        observation = []
        position = np.array(observation_data[robot_id]['pipette_position'], dtype=np.float32)
        observation = np.concatenate([position, self.goal_position])

        reward, distance = self.compute(observation)
        terminated, termination_reason, bonus = self.check_termination(distance)
        reward += bonus

        truncated = self.steps >= self.max_steps
        info = {
            'Truncated': 'Max steps reached' if truncated else None,
            'Terminated': termination_reason if terminated else None,
            'Pipette coordinates': observation[:3],
            'Distance from goal': distance,
            'Reward': reward
        }

        self.steps += 1
        return observation, reward, terminated, truncated, info


    def render(self, mode='human'):
        pass

    def compute(self, observation):
        """Computes the reward for the Reinforcement learning model

        Args:
            observation (List): Contains the x, y, z of the pipette and goal location

        Returns:
            reward, np.float32: The reward for the model
        """
        # Eucludian distance, hell yeah https://www.tiktok.com/@sivartstock/video/7264039747142618373
        distance = np.linalg.norm(observation[:3] - observation[3:6])
        previous_distance = getattr(self, 'previous_distance', distance)
        reward = previous_distance - distance  # Reward improvement
        self.previous_distance = distance  # Update for next step
        return reward, distance



    def check_termination(self, distance):
        """Checks if the distance is within the distance_threshold

        Args:
            distance (np.float32): _description_

        Returns:
            Terminated, bool: If the model has been terminated or not
            Terminated_reason, string: Reason of termination
        """
        if distance < self.distance_threshold:
            reward = 100
            return True, "goal_reached", reward
        return False, None, 0
    
    def close(self):
        """Closes the simulation
        """
        self.sim.close()

class RewardShapingCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(RewardShapingCallback, self).__init__(verbose)

    def _on_step(self) -> bool:
        env = self.training_env.envs[0]
        if isinstance(env, OT2_wrapper):
            env.distance_threshold = max(0.0001, env.distance_threshold * 0.999)
            # Adjust reward multiplier
            env.reward_scale = getattr(env, 'reward_scale', 1.0) * 1.01


        return True
    
class CurriculumCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(CurriculumCallback, self).__init__(verbose)
        self.success_buffer = []
        self.target_success_rate = 0.8  # Aim for 80% success rate
        self.buffer_size = 100  # Sliding window size for calculating success rate

    def _on_step(self) -> bool:
        # Access the environment
        env = self.training_env.envs[0]  # Assuming a single environment
        if isinstance(env, OT2_wrapper):
            # Check if the current episode ended with success
            success = any(info.get("Terminated") == "goal_reached" for info in self.locals["infos"])
            self.success_buffer.append(success)

            # Keep the buffer size fixed
            if len(self.success_buffer) > self.buffer_size:
                self.success_buffer.pop(0)

            # Calculate success rate and update the distance threshold
            if len(self.success_buffer) == self.buffer_size:
                success_rate = sum(self.success_buffer) / self.buffer_size
                env.update_distance_threshold(success_rate)

        return True


class AdaptiveThresholdCallback(BaseCallback):
    def __init__(self, verbose=0):
        super(AdaptiveThresholdCallback, self).__init__(verbose)
        self.target_success_rate = 0.8  # Aim for 80% success rate
        self.success_buffer = []

    def _on_step(self) -> bool:
        env = self.training_env.envs[0]
        if isinstance(env, OT2_wrapper):
            success = any(info.get("Terminated") == "goal_reached" for info in self.locals["infos"])
            self.success_buffer.append(success)

            # Adjust distance threshold based on recent success rate
            if len(self.success_buffer) > 100:  # Buffer size
                success_rate = sum(self.success_buffer) / len(self.success_buffer)
                if success_rate > self.target_success_rate:
                    env.distance_threshold *= 0.99  # Make task harder
                else:
                    env.distance_threshold *= 1.01  # Make task easier
                self.success_buffer.pop(0)
        return True


if __name__ == '__main__':
    from stable_baselines3.common.env_checker import check_env

    # instantiate your custom environment
    wrapped_env = OT2_wrapper() # modify this to match your wrapper class

    # Assuming 'wrapped_env' is your wrapped environment instance
    check_env(wrapped_env)