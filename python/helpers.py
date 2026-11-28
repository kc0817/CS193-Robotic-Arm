import math

from ikpy.chain import Chain
import matplotlib.pyplot as plt

def save_current_plot(currents: list[float], times: list[float]):
    plt.plot(times, currents)
    plt.title("Grabber Current Over Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Current (mA)")
    plt.savefig("current_graph.png")


def print_list(l: list):
    for line in l:
        print(line)
def to_rad(n: float) -> float:
    return n * math.pi / 180
def to_deg(n: float) -> float:
    return n * 180 / math.pi

def calc_fk(chain: Chain, joint_targets: list[float]) -> tuple[float, float]:
    
    angles_list_rad = [to_rad(joint_targets[i]) for i in range(len(joint_targets)-1)] # don't include grabber state
    angles_list_rad.insert(0, None)
    angles_list_rad.append(None)
    T = chain.forward_kinematics(angles_list_rad)
    pos = T[:3, 3]
    tip_dir = T[:3, 2]
    pitch = math.atan2(tip_dir[2], math.sqrt(tip_dir[0]**2 + tip_dir[1]**2))
    return pos, to_deg(pitch)