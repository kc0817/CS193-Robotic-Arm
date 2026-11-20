import math

from ikpy.chain import Chain


def print_list(l: list):
    for line in l:
        print(line)
def to_rad(n: float) -> float:
    return n * math.pi / 180
def to_deg(n: float) -> float:
    return n * 180 / math.pi

# def calc_fk(turret_angle, shoulder_angle, elbow_angle, wrist_pitch_angle, ):
#     a0 = to_rad(turret_angle)
#     a1 = to_rad(shoulder_angle)
#     a2 = to_rad(elbow_angle)
#     a3 = to_rad(wrist_pitch_angle)
#     l1 = chain.links[3].origin_translation[2]
#     l2 = chain.links[4].origin_translation[2]
#     l3 = chain.links[5].origin_translation[2] + chain.links[6].origin_translation[2]
#     r = l1*math.sin(a1) + l2*math.sin(a1+a2) + l3*math.sin(a1+a2+a3)
#     z = l1*math.cos(a1) + l2*math.cos(a1+a2) + l3*math.cos(a1+a2+a3) + chain.links[1].origin_translation[2] + chain.links[2].origin_translation[2]
#     x = r * math.cos(a0)
#     y = r * math.sin(a0)
#     fk_pitch = a0 + a1 + a2

def calc_fk(chain: Chain, joint_targets: list[float]) -> tuple[float, float]:
    
    angles_list_rad = [to_rad(joint_targets[i]) for i in range(len(joint_targets)-1)] # don't include grabber state
    angles_list_rad.insert(0, None)
    angles_list_rad.append(None)
    T = chain.forward_kinematics(angles_list_rad)
    pos = T[:3, 3]
    tip_dir = T[:3, 2]
    pitch = math.atan2(tip_dir[2], math.sqrt(tip_dir[0]**2 + tip_dir[1]**2))
    return pos, to_deg(pitch)