from grpc import Status
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from sim_class import Simulation
import pybullet as p


class OT2_wrapper(gym.Env):
    def __init__(self, render=False, max_steps=1000):
        # Calls the constructor off the parent class while being bound to the instance of this wrapper
        super(OT2_wrapper, self).__init__()

        # Overwrites render method but I do not know why, The mentors provided this
        self.render = render 
        self.distance_threshold = 3.9e-3

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
        low_bound = [-0.187, -0.1705, 0.1695]
        high_bound = [0.253, 0.2195, 0.2908]

        # Generates a 3 random numbers according to the observation space definition
        self.goal_position = np.random.uniform(low=low_bound, high=high_bound, size=(3,))

        # This resets the simulation so it always has a fresh start
        status = self.sim.reset(num_agents=1)

        # If the simulation has multiple agents the robotID are different and the ID might change between resets, For this reason the keys are gotten
        # We only need the first one because the wrapper is made to only support a single agent per simulation
        robot_id = list(status.keys())[0]

        # Observation is set to the pipette position and goal is appended, This results in a array of (6,) np.float32's
        observation = np.array(status[robot_id]['pipette_position'])
        observation = np.concatenate([observation, self.goal_position])

        # Everytime the simulation is reset for whatever reason the current amount of used steps need to be reset
        self.steps = 0

        # The Gymnasium expects the observations to be returned and a dictionary with info, We do not provide any info in this fuction so a empty dictionary is returned to avoid errors
        return observation, {}


    def step(self, action):
        """Controls the steps and training flow of the reinforcement model

        Args:
            action (List[List]): A list of list containing the x, y and z velocities of the OT2 robot

        Returns:
            Observation, List: Contains the xyz coordinates of the pipette and goal
            reward, np.float32: The calculated reward for the model
            terminated, bool: If the episode has been terminated or not
            truncated, bool: If the episode has been truncated or not
            info, dict: Information about termination, truncation or information about the current progress of the episode
        """
        # Execute one time step within the environment
        # since we are only controlling the pipette position, we accept 3 values for the action and need to append 0 for the drop action
        action = np.append(action, 0)

        # Call the environment step function
        # Action is passed on as a list because the apply_actions method in sim_class uses this list to define actions for multiple agents
        observation = self.sim.run([action])

        # as np.array get pipette coordinates
        robot_id = list(observation.keys())[0]

        # 
        observation = np.array(observation[robot_id]['pipette_position'])

        observation = np.concatenate([observation, self.goal_position])

        # EXPERIMENT HERE <3
        reward, distance = self.compute_reward(observation)

        terminated, termination_reason = self.check_termination(reward)

        # Truncate the training episode if the maximum of steps is reached
        # Because the step() function requires a dictionary to be returned with info no matter the outcome we return some useful information
        if self.steps == self.max_steps:
            truncated = True
            info = {'Truncated': 'Max steps reached'}
        else:
            truncated = False

        if terminated:
            info = {'Terminated': termination_reason}

        # If the process is not truncated or terminated we return information about the progress of the model
        if not terminated and not truncated:
            info = {'Pipette coordinates': observation[:3], 'Distance from goal': distance, 'Reward': reward}

        self.steps += 1

        return observation, reward, terminated, truncated, info

    def render(self, mode='human'):
        pass

    def compute_reward(self, observation):
        """Computes the reward for the Reinforcement learning model

        Args:
            observation (List): Contains the x, y, z of the pipette and goal location

        Returns:
            reward, np.float32: The reward for the model
        """
        # Eucludian distance, hell yeah https://www.tiktok.com/@sivartstock/video/7264039747142618373
        distance = np.linalg.norm(observation[:3] - observation[3:6])
        distance_penalty = distance

        return -distance_penalty, distance


    def check_termination(self, distance):
        """Checks if the distance is within the distance_threshold

        Args:
            distance (np.float32): _description_

        Returns:
            Terminated, bool: If the model has been terminated or not
            Terminated_reason, string: Reason of termination
        """
        if distance < self.distance_threshold:
            return True, "goal_reached"
        return False, None
    
    def close(self):
        """Closes the simulation
        """
        self.sim.close()

# class GoalVisualizer:
#     def __init__(self, simulation):
#         """
#         Initialize the visualizer with a PyBullet simulation object.
#         """
#         self.sim = simulation
#         self.goal_marker_ids = []  # To track debug items for cleanup

#     def draw_goal(self, goal_position, radius=0.05, color=[0, 1, 0]):
#         """
#         Draws a simple representation of the goal as crosshairs in the PyBullet simulation.
#         """
#         # Clear previous markers
#         self.clear_goal_markers()

#         # Draw crosshairs to represent the goal position
#         axis_lines = [
#             ([goal_position[0] - radius, goal_position[1], goal_position[2]],
#             [goal_position[0] + radius, goal_position[1], goal_position[2]]),
#             ([goal_position[0], goal_position[1] - radius, goal_position[2]],
#             [goal_position[0], goal_position[1] + radius, goal_position[2]]),
#             ([goal_position[0], goal_position[1], goal_position[2] - radius],
#             [goal_position[0], goal_position[1], goal_position[2] + radius]),
#         ]

#         for start, end in axis_lines:
#             marker_id = p.addUserDebugLine(start, end, lineColorRGB=color, lineWidth=2.0)
#             self.goal_marker_ids.append(marker_id)


#     def clear_goal_markers(self):
#         """
#         Removes all previous goal markers from the simulation.
#         """
#         for marker_id in self.goal_marker_ids:
#             p.removeUserDebugItem(marker_id)
#         self.goal_marker_ids = []


if __name__ == '__main__':
    from stable_baselines3.common.env_checker import check_env

    # instantiate your custom environment
    wrapped_env = OT2_wrapper([0.05, 0.7]) # modify this to match your wrapper class

    # Assuming 'wrapped_env' is your wrapped environment instance
    check_env(wrapped_env)