from sim_class import Simulation
import pybullet as p
import numpy as np
import imageio

sim = Simulation(num_agents=1, rgb_array=True)

def torque_exceeds_threshold(torque, threshold=500):
    print(torque)
    return abs(torque) > threshold

def generate_actions(vel_x, vel_y, vel_z, drop):
    return [[vel_x, vel_y, vel_z, drop]]

def get_boundaries(simulation, robot_id):
    boundaries = {"x_min": None, "x_max": None, "y_min": None, "y_max": None}

    frames = []  # List to store captured frames

    while True:
        actions = generate_actions(0.0, 0.0, 0.0, 0)
        status = sim.run(actions)
        joint_states = status['robotId_1']['joint_states']
        torque_state_joint_0 = joint_states['joint_0']['motor_torque']

        torque_above_thres_counter = 0

        while torque_above_thres_counter <= 10:
            actions = generate_actions(0.8, 0.0, 0.0, 0)
            status = sim.run(actions, num_steps=1)
            joint_states = status['robotId_1']['joint_states']
            torque_state_joint_0 = joint_states['joint_0']['motor_torque']

            # Capture the frame after each step
            img = sim.get_frame()
            frames.append(img)  # Add frame to the list

            if torque_exceeds_threshold(torque_state_joint_0):
                torque_above_thres_counter += 1

        boundaries["x_max"] = status['robotId_1']['robot_position'][0]

        torque_above_thres_counter = 0
        actions = generate_actions(-0.8, 0.0, 0.0, 0)
        status = sim.run(actions, num_steps=1)
        joint_states = status['robotId_1']['joint_states']
        torque_state_joint_0 = joint_states['joint_0']['motor_torque']

        while torque_above_thres_counter <= 10:
            actions = generate_actions(-0.8, 0.0, 0.0, 0)
            status = sim.run(actions, num_steps=1)
            joint_states = status['robotId_1']['joint_states']
            torque_state_joint_0 = joint_states['joint_0']['motor_torque']

            # Capture the frame after each step
            img = sim.get_frame()
            frames.append(img)  # Add frame to the list

            if torque_exceeds_threshold(torque_state_joint_0):
                torque_above_thres_counter += 1

        boundaries["x_min"] = status['robotId_1']['robot_position'][0]

        torque_above_thres_counter = 0
        actions = generate_actions(0.8, 0.0, 0.0, 0)
        status = sim.run(actions, num_steps=1)
        joint_states = status['robotId_1']['joint_states']
        torque_state_joint_1 = joint_states['joint_1']['motor_torque']

        while torque_above_thres_counter <= 10:
            actions = generate_actions(0.0, 0.8, 0.0, 0)
            status = sim.run(actions, num_steps=1)
            joint_states = status['robotId_1']['joint_states']
            torque_state_joint_1 = joint_states['joint_1']['motor_torque']

            # Capture the frame after each step
            img = sim.get_frame()
            frames.append(img)  # Add frame to the list

            if torque_exceeds_threshold(torque_state_joint_1):
                torque_above_thres_counter += 1

        boundaries["y_max"] = status['robotId_1']['robot_position'][1]

        torque_above_thres_counter = 0
        actions = generate_actions(0.0, -0.8, 0.0, 0)
        status = sim.run(actions, num_steps=1)
        joint_states = status['robotId_1']['joint_states']
        torque_state_joint_1 = joint_states['joint_1']['motor_torque']

        while torque_above_thres_counter <= 10:
            actions = generate_actions(0.0, -0.8, 0.0, 0)
            status = sim.run(actions, num_steps=1)
            joint_states = status['robotId_1']['joint_states']
            torque_state_joint_1 = joint_states['joint_1']['motor_torque']

            # Capture the frame after each step
            img = sim.get_frame()
            frames.append(img)  # Add frame to the list

            if torque_exceeds_threshold(torque_state_joint_1):
                torque_above_thres_counter += 1

        boundaries["y_min"] = status['robotId_1']['robot_position'][1]

        torque_above_thres_counter = 0
        actions = generate_actions(0.0, 0.8, 0.0, 0)
        status = sim.run(actions, num_steps=1)
        joint_states = status['robotId_1']['joint_states']
        torque_state_joint_1 = joint_states['joint_1']['motor_torque']

        break

    # Save captured frames as a GIF
    if frames:
        print(len(frames))
        #frames = [f for i, f in enumerate(frames) if i % 40 == 0]
        imageio.mimsave('simulation.gif', frames, duration=0.5)

    return boundaries

if __name__ == '__main__':
    actions = generate_actions(-0.5,0.5, 0, 1)
    sim.run(actions, num_steps=200)
    frame = sim.current_frame
    print('frame shape:', frame.shape)
    imageio.mimsave('simulation.gif', frame, duration=0.5)


    print(frame)

    #boundaries = get_boundaries(sim, 'robotId_1')
    #print(boundaries)
