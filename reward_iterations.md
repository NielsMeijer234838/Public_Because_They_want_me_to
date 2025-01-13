# Iterations for reward functions

## Iteration 1

```python
reward = -np.linalg.norm(pipette_pos - goal_pos)
```

This takes the eucludian distance between the current position and the goal position.

## Iteration 2

```python
    def step(self, action):
        # Execute one time step within the environment
        # since we are only controlling the pipette position, we accept 3 values for the action and need to append 0 for the drop action

        action = np.append(action, 0)

        # Call the environment step function
        # Action is passed on as a list because the apply_actions method in sim_class uses this list to define actions for multiple agents.
        status = self.sim.run([action])

        # as np.array get pipette coordinates.
        robot_id = list(status.keys())[0]

        torques = [abs(joint_info['motor_torque']) for joint_info in status[robot_id]['joint_states'].values()]

        observation = np.array(status[robot_id]['pipette_position'])

        observation = np.concatenate([observation, self.goal_position])

        # EXPERIMENT HERE <3
        reward = self.compute_reward(observation, torques)

        # Check termination conditions
        terminated, termination_reason = self.check_termination(reward, torques)

        if terminated:
            info = {'Terminated': termination_reason}

        if self.steps == self.max_steps:
            truncated = True
            info = {'Truncated': 'Max steps exceeded'}
        else:
            truncated = False

        if not info:
            info = {'coordinates': observation[:3], 'reward': reward}


        self.steps += 1

        return observation, reward, terminated, truncated, info

    def compute_reward(self, observation, torques):
        distance = np.linalg.norm(observation[:3] - observation[3:6])
        distance_penalty = distance
        torque_penalty = sum(torques) * 0.001  # Scale appropriately

        # Add a positive reward for being close to the goal
        if distance < 0.01:  # Goal tolerance threshold
            goal_bonus = 10.0
        elif distance < 0.2:
            goal_bonus = 5.0
        else:
            goal_bonus = 0.0

        return -distance_penalty * 2 - torque_penalty + goal_bonus
```

abstracted into a new fuction and calculates the eucludian distance, gives a penalty for high torque (very small and unnecessary) and a step wise bonus for coming within a certain amount of distance.

This seems to fail as a flat bonus is enough to start dopamine maxxing instead of achieving the goal.

## Potential iteration 3

After some discussion with Jason van Hammond he used this function. We discovered some flaws however.

```python
    def compute_reward(self, observation)
        # Eucludian distance
        distance = np.linalg.norm(pipette_position - self.goal_position)

        # If previous distance is not set, set it
        if not hasattr(self, "previous_distance"):
            self.previous_distance = distance
            self.initial_distance = distance

        # Small reward for getting closer
        progress_reward = (self.previous_distance - distance) * 10

        # Resets previous distance for next reward
        self.previous_distance = distance

        # Percentage based milestones
        milestones = [0.25, 0.5, 0.75]
        milestone_reward = 0
        for milestone in milestones:
            # If previous distance is greater than milestone and current distance smaller than a milestone distance give extra reward
            # This function is bugged however and always gives a milestone reward once a milestone has been reached
            # Milestones should be popped from the array so they cant be abused
            if self.previous_distance > milestone * self.initial_distance and distance <= milestone * self.initial_distance:
                milestone_reward += 20
        reward = progress_reward + milestone_reward + -0.01

        return reward
```

This can be solved by popping the milestone that has been reached after it has been given the reward. This ensures a reward for a milestone cannot be given twice. Milestones is moved to the class constructor and assigned to it. This is so the milestones dont keep getting set after popping. The loop gets slightly changed:

```python
for milestone in milestones[:]:
    # If previous distance is greater than milestone and current distance smaller than a milestone distance give extra reward
    # Milestones are popped from the array so they cant be abused
    if self.previous_distance > milestone * self.initial_distance and distance <= milestone * self.initial_distance:
        milestone_reward += 20
        self.milestones.remove(milestone)

# Resets previous distance for next reward
self.previous_distance = distance
```

And with the other variables within the class constructor we do this:

```python
    def __init__(self, render=False, max_steps=1000):
        super(OT2_wrapper, self).__init__()
        self.render = render
        self.max_steps = max_steps
        self.goal_position = None
        self.milestones = [round(i * 0.05, 2) for i in range(20)]
```

or for testing purposes we can also pass the milestones as a parameter to the constructor instead. This way we can test a few milestone ranges to see if which increments work best.

```python
    def __init__(self, render=False, max_steps=1000, milestones):
        super(OT2_wrapper, self).__init__()
        self.render = render
        self.max_steps = max_steps
        self.goal_position = None
        self.milestones = milestones
```


