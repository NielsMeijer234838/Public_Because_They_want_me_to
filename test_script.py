import gymnasium as gym
import numpy as np
from ot2_gym_wrapper import OT2_wrapper
import matplotlib.pyplot as plt

def plot_path(path_taken):
    x, y, z = zip(*path_taken)

    x = list(x)
    y = list(y)
    z = list(z)

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d') 

    ax.plot(x, y, z, color='b', marker='o', linestyle='-', label='Robot Path')

    # Highlight the first and last points
    ax.scatter(x[0], y[0], z[0], color='g', s=100, label='Start Point', marker='^')  # First point (start)
    ax.scatter(x[-1], y[-1], z[-1], color='r', s=100, label='End Point', marker='v')  # Last point (end)

    ax.set_title("Robot Path in 3D Space")
    ax.set_xlabel("X-axis")
    ax.set_ylabel("Y-axis")
    ax.set_zlabel("Z-axis")
    ax.legend()

    plt.show()

# Load your custom environment
env = OT2_wrapper(max_steps=100)

# Number of episodes
num_episodes = 5

for episode in range(num_episodes):

    path = []

    obs = env.reset()

    path.append(obs[0:3])

    done = False
    step = 0

    while not done:
        # Take a random action from the environment's action space
        action = env.action_space.sample()
        obs, reward, terminated, truncated, info = env.step(action)

        if terminated or truncated:
             done = True

        path.append(obs[0:3])

        print(f"Episode: {episode + 1}, Step: {step + 1}, Action: {action}, Reward: {reward}")

        step += 1
        if done:
            print(f"Episode finished after {step} steps. Info: {info}")

            plot_path(path)
            break
