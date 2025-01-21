import wandb
from wandb.integration.sb3 import WandbCallback
from ot2_gym_wrapper import OT2_wrapper, RewardShapingCallback, AdaptiveThresholdCallback, CurriculumCallback
from stable_baselines3 import PPO
import os
import argparse
from clearml import Task
from typing_extensions import TypeIs
import tensorflow
from stable_baselines3.common.callbacks import CallbackList
from itertools import product

parser = argparse.ArgumentParser()
parser.add_argument("--learning_rate", type=float, default=0.0003)
parser.add_argument("--batch_size", type=int, default=64)
parser.add_argument("--n_steps", type=int, default=2048)
parser.add_argument("--n_epochs", type=int, default=10)

args = parser.parse_args()

task = Task.init(project_name='Mentor Group J/Group 3', # NB: Replace YourName with your own name
                     task_name='adjusted bounds')

task.set_base_docker('deanis/2023y2b-rl:latest')

task.execute_remotely(queue_name="default")

os.environ['WANDB_API_KEY'] = '118175988af2b259ce56714ba8a38955d33c1939'

env = OT2_wrapper(max_steps=1000)
model = PPO('MlpPolicy', env, verbose=1)

# initialize wandb project
run = wandb.init(project="test",sync_tensorboard=True) # sb3_OT2

#create wandb callback
wandb_callback = WandbCallback(model_save_freq=20000,
                                model_save_path=f"models/{run.id}",
                                verbose=2,
                                )

dynamic_distance_reward = RewardShapingCallback()
dynamic_speed_reward = AdaptiveThresholdCallback()
curriculum_callback = CurriculumCallback()

model.learn(total_timesteps=5000000, callback=[dynamic_distance_reward, curriculum_callback, wandb_callback], 
            progress_bar=True, reset_num_timesteps=False, 
            tb_log_name=f"runs/{run.id}")

# Define the possible values for n_steps
#n_steps_values = [1024, 2048]

# # Define the list of callbacks (excluding wandb_callback as it's always added)
# callbacks = [dynamic_distance_reward, dynamic_speed_reward, [dynamic_distance_reward, dynamic_speed_reward]]

# # Create all combinations of callbacks and n_steps values
# callback_combinations = list(product(callbacks, n_steps_values))
# print(len(callback_combinations))

# # Loop through all combinations of callbacks and n_steps
# for cb, n_steps in callback_combinations:
#     # Initialize a new wandb run for each combination
#     run = wandb.init(project="sb3_OT2", sync_tensorboard=True, reinit=True)  # reinit=True creates a new run

#     if not os.path.exists(f"models/{run.id}"):
#         os.makedirs(f"models/{run.id}")

#     # Add the W&B callback explicitly for each combination
#     wandb_callback = WandbCallback(model_save_freq=200000,
#                                     model_save_path=f"models/{run.id}",
#                                     verbose=2,
#                                     )
        
#     if isinstance(cb, list):
#         current_callbacks = cb + [wandb_callback]  # Add wandb callback explicitly
#     else:
#         current_callbacks = [cb, wandb_callback] # Add wandb callback explicitly

#     # Initialize the model with the current n_steps value
#     model = PPO('MlpPolicy', env, verbose=1, 
#                 learning_rate=args.learning_rate, 
#                 batch_size=args.batch_size, 
#                 n_steps=n_steps,  # Set n_steps from the combination
#                 n_epochs=args.n_epochs, 
#                 tensorboard_log=f"runs/{run.id}",)

#     # Log the callback configuration to WandB
#     callback_names = [type(cb).__name__ for cb in current_callbacks]

#     # Log the number of steps
#     wandb.log({"n_steps": n_steps})

#     # Create the table with rows as lists of callback names
#     callback_table = wandb.Table(columns=["Callbacks used"], data=[[cb] for cb in callback_names])

#     # Log the table
#     wandb.log({"callbacks_table": callback_table})

#     # Train the model
#     model.learn(total_timesteps=5000000, callback=current_callbacks, 
#                 progress_bar=True, reset_num_timesteps=False, 
#                 tb_log_name=f"runs/{run.id}")

#     # Finish the run
#     wandb.finish()

        