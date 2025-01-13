# Pybullet simulation environment
 
## Python requirements

For the simulation environment to work several packages should be installed within python.

| Package   | Version  |
|-----------|----------|
| python     | 3.10.16 |
| numpy      | 1.26.4  |
| pillow     | 11.0.0  |
| pybullet   | 3.25    |
| tk         | 8.6.14  |
| imageio    | 2.33.1  |

A full list of the entire enviroment can be found in [requirements.txt](requirements.txt).

## Getting the digital twin.

The digital twin can be cloned from [github](https://github.com/BredaUniversityADSAI/Y2B-2023-OT2_Twin.git) using the command:

```
git clone https://github.com/BredaUniversityADSAI/Y2B-2023-OT2_Twin.git
```
The content of this folder can be copied into a different folder if wished after cloning.

## The code

Within the `sim_class.py` file the digital twin of the OT-2 is defined. This class is imported with the line `from sim_class import Simulation`. This will allow you to access all the functions in the `simulation` class.

### Functions

#### Constructor

The constructor of the `Simulation` class takes a a variety of arguments.

| arg | optional | dtype | default | function |
|-----|----------|-------|---------|----------|
| num_agents | Required | int | N/A | This is the number of instances you want to create of the digital twin. |
| render | Optional | bool | True | This flag tells pybullet to give a graphical user interface. This takes more computing power and can slow down the simulation. |
| rgb_array | optional | bool | False | This tells the program to save the current frame in the `run()` method into `current_frame`. |

#### reset(num_agents)

Resets the current simulation by deleting all instances and sets up new instances of the digital twin.

| arg | optional | dtype | default | function |
|-----|----------|-------|---------|----------|
| num_agents | Required | int | N/A | This is the number of instances you want to create of the digital twin. |

#### run(actions, num_steps)

Runs the provided actions a number of times.

| arg | optional | dtype | default | function |
|-----|----------|-------|---------|----------|
| actions | Required | list[float], length 4 | N/A | This parameter describes how the robot should behave. The array represents the following `[velocity_x, velocity_y, velocity_z, drop]`. The velocities can be positive or negative intergers depending on which direction the robot needs to move. Each interger represents the speed. Drop can be either `1` or `0` if a droplet should be dispensed or not within the action. |
| num_steps | Optional | int | 1 | Tells the function how many times the provided action should be repeated. |

Limitations: If you want to record the simulation num_steps can only be 1 as only one frame is stored in the class memory. You can run multiple steps however the result of the last one is recorded.

returns: Dict[str, Dict[str, Dict[str, Dict[str, float]]]]
Example output

```
{'robotId_1': 
    {'joint_states':    
        {'joint_0':
            {'position': 0.00777527420584602, 
             'velocity': 0.09759142889915198, 
             'reaction_forces': (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 
             'motor_torque': 500.00000000000006}, 
         'joint_1': 
            {'position': 0.010336465117466921, 
             'velocity': -0.13164565537412717, 
             'reaction_forces': (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 
             'motor_torque': -500.00000000000006}, 
         'joint_2': 
            {'position': 0.04944985139747543, 
            'velocity': 0.032879858798796784, 
            'reaction_forces': (0.0, 0.0, 0.0, 0.0, 0.0, 0.0), 
            'motor_torque': -800.0}}, 
    'robot_position': [-0.007775245944157955, -0.010336456274825498, 0.07944984940836988], 
    'pipette_position': [0.0652, 0.0792, 0.1689]}}
```

| joint | axis |
|-------|------|
| joint_0 | x    |
| joint_1 | y    |
| joint_2 | z    |

The boundries of the robot are:

| corner             | x       | y       | z       |
|--------------------|---------|---------|---------|
| bottom_front_left  | 0.253   | -0.1708 | 0.1695  |
| bottom_front_right | 0.253   | 0.2195  | 0.1694  |
| bottom_back_left   | -0.187  | -0.1705 | 0.1688  |
| bottom_back_right  | -0.187  | 0.2198  | 0.1695  |
| top_front_left     | 0.253   | -0.1705 | 0.2899  |
| top_front_right    | 0.2539  | 0.2195  | 0.2895  |
| top_back_left      | -0.187  | -0.1705 | 0.2908  |
| top_back_right     | -0.187  | 0.2195  | 0.2899  |

This information can be gathered using the methods discussed in [this section](#interacting-with-the-simulation).



#### set_start_position(x, y, z)

Iterates through each digital twin instance and sets their coordinates based on their location on the grid.

| arg | optional | dtype | default | function |
|-----|----------|-------|---------|----------|
| x   | Required | float | N/A     | Sets the x coordinate. |
| y   | Required | float | N/A     | Sets the y coordinate. |
| z   | Required | float | N/A     | Sets the z coordinate. |

#### get_pipette_position(robotId)

Given a single robotId gets the pipette position of the robot.

| arg | optional | dtype | default | function |
|-----|----------|-------|---------|----------|
| robotId | Required | str | N/A | Identifies the robot by id. |

returns: The current pipette location of `robotId` as array `[x, y, z]`

### Interacting with the simulation.

As a example on how to interact with the simulation we are going to touch the 8 limit points within the cube using the pipette, print out the machine status and log the robots current actions.

To do this we are first setting up our simulation and create a single instance of the robot.

```
from sim_class import Simulation

# We want to capture the simulation to display afterwards. if not leave rgb_array as false
sim = Simulation(num_agents=1, rgb_array=True)
```

Now we have a global variable called `sim` which we will use to interact with the simulation.


We will use 2 functions to move the robot to each corner.

```
def generate_action(vel_x, vel_y, vel_z, drop):
    return [[vel_x, vel_y, vel_z, drop]]
```

`generate_action` takes in the desired velocity to move in each direction and if it during the action it should drop or not. It returns this in the desired format for the `Simulation` class.

```
def move(simulation, actions, steps=1):
    status = simulation.run(actions, num_steps=steps)
    return status
```

This will sent the instance of the `Simulation`, the `actions` generated by the `generate_action` function and optionally `steps`. In our example since we want to output a gif of the simulation we will always have `steps = 1`.

We define a array for all the frames for the gif and call `Simulation.run()` with actions that dont do anything. This is done just to give a simple output and initialise status with some information.

From here on out we have while loops like this.
We check if the torque on the motors is above a certain threshold for 10 times. Sometimes during moving in a direction due to speedup the torque spikes. Otherwise the torque is a great indication that the motor is currently trying to go somewhere it can not go.

```
while under_threshold_counter <= 10:
    status = sim.run(actions)
    torque = abs(status['robotId_1']['joint_states']['joint_0']['motor_torque'])

    if torque >= 500:
        under_threshold_counter += 1

    frames.append(sim.current_frame)
```

Once it reaches an edge we can dump the coordinates using `status['robotId_1']['pipette_position']`

during each step of the while loop the frames are appended to an array and we can use packages like `imageio` to save it.

```
imageio.mimsave('corner_touching.gif', frames, duration=0.5)
```

With the result being:

![Gif of touching each corner](corner_touching.gif "robot simulation")

![Path taken by the robot.](Path_taken.png "A graph of the taken path by the digital twin.")
