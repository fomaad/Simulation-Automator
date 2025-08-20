import os
import itertools
import shutil
from pathlib import Path

# root paths
project_root = Path("/path/to/project")
autoware_root = Path("/path/to/autoware") #eg. /home/user/autoware

# paths
script_template_path = project_root / "cutout/temp/cutoutTemp.script"
log_file = project_root / "cutout/temp/simulation_log.csv"
output_dir = project_root / "cutout/output"

config_path = autoware_root / "src/launcher/autoware_launch/autoware_launch/config/planning/scenario_planning/common/common.param.yaml"

EGO_OFFSET = 5

distances = list(range(0, 65, 5))
dx_values = [EGO_OFFSET + d for d in distances]

ve_table = {
    10: 2.778, 20: 5.556, 30: 8.333, 40: 11.111, 50: 13.889
}

lat_table = {
    10:1.0, 
    11:1.1, 12:1.2, 13:1.3, 14:1.4, 15:1.5, 16:1.6, 17:1.7, 18:1.8, 19:1.9, 20:2.0, 
    21:2.1, 22:2.2, 23:2.3, 24:2.4, 25:2.5, 26:2.6, 27:2.7, 28:2.8, 29:2.9, 30:3.0
}


#Overwrite the temp script
def generate_script(dx, ve, lat):

    match ve:
        case 2.778: activation_distance = 60
        case 5.556: activation_distance = 100
        case 8.333: activation_distance = 120
        case 11.111: activation_distance = 170
        case 13.889: activation_distance = 198
        case 16.67: activation_distance = 220
        case _: print("error in reading ve")

    if ve<=11.11 :
        return f'''
spawnPos = "TrafficLane.112";
goal = "TrafficLane.111" at 220;
dx = {dx};
ve = {ve};
lat = {lat};
activation_distance = {activation_distance};
route1 = [
    "TrafficLane.112" max-velocity(ve),
    cut-out(activation_distance, ve, lat, dx),
    "TrafficLane.111" max-velocity(ve)
];

npc1 = NPC("hatchback", spawnPos forward 20, goal, route1, [acceleration(1), delay-move-until-ego-engaged(1)]);
npc2 = NPC("hatchback", _, [delay-spawn(_)]);

ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos, "TrafficLane.112" at 190, [max-velocity(ve)]);

run("Shinjuku", ego, [npc1,npc2], [saving-timeout(50)]);

        '''
    else:
        return f'''
spawnPos = "TrafficLane.112";
goal = "TrafficLane.277" at 20;
dx = {dx};
ve = {ve};
lat = {lat};
activation_distance = {activation_distance};
route1 = [
    "TrafficLane.112" max-velocity(ve),
    cut-out(activation_distance, ve, lat, dx),
    "TrafficLane.111" max-velocity(ve),
    "TrafficLane.113" max-velocity(ve),
    "TrafficLane.277" max-velocity(ve)
];

npc1 = NPC("hatchback", spawnPos forward 25, goal, route1, [acceleration(1), delay-move-until-ego-engaged(1)]);
npc2 = NPC("hatchback", _, [delay-spawn(_)]);

ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos, "TrafficLane.122" at 20, [max-velocity(ve)]);

run("Shinjuku",ego, [npc1,npc2], [saving-timeout(60)]);

        '''

#overwrite autoware config to change global speed limit
def generate_config(ve):
    return f'''/**:
  ros__parameters:
    max_vel: {ve}      # max velocity limit [m/s]

    # constraints param for normal driving
    normal:
      min_acc: -8.3         # min deceleration [m/ss]
      max_acc: 8.0          # max acceleration [m/ss]
      min_jerk: -1.0       # min jerk [m/sss]
      max_jerk: 83.3         # max jerk [m/sss]

    # constraints to be observed
    limit:
      min_acc: -7.59         # min deceleration limit [m/ss]
      max_acc: 8.0          # max acceleration limit [m/ss]
      min_jerk: -1.2        # min jerk limit [m/sss]
      max_jerk: 12.65        # max jerk limit [m/sss]
'''

def write_script_to_temp(script_text):
    with open(script_template_path, "w") as f:
        f.write(script_text)

def write_script_to_config(config_text):
    with open(config_path, "w") as f:
        f.write(config_text)

combinations = list(itertools.product(dx_values, ve_table.items(), lat_table.items()))
print(f"Total combinations: {len(combinations)}")

# Load already simulated tags
completed = set()
if os.path.exists(log_file):
    with open(log_file, "r") as log:
        completed = {line.strip() for line in log if line.strip()}

# Determine next simulation
run_queue = []
for dx, (v_kmh, ve), (lat_label, lat) in combinations:
    dist = round(dx - EGO_OFFSET)
    tag = f"cutout{dist}-{v_kmh}-{lat_label}"
    if tag not in completed:
        run_queue.append((dx, ve, v_kmh, lat_label, lat, dist, tag))

print(f"Remaining to simulate: {len(run_queue)}")

#when queue is not empty run the next one
if len(run_queue)>0:
    dx, ve, v_kmh, lat_label, lat, dist, tag = run_queue[0]
    print(f"Preparing simulation: {tag}")
    script_text = generate_script(dx, ve, lat)
    config_text = generate_config(ve)
    write_script_to_config(config_text)
    write_script_to_temp(script_text)
    print(tag)  # pass tag to bash
else:
    print("All combinations simulated.")
