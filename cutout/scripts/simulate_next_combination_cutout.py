import os
import itertools
import shutil
from pathlib import Path

# root paths
project_root = Path("/path/to/project")
autoware_root = Path("/path/to/autoware") #eg. /home/user/autoware

# paths
script_template_path = project_root / "cutin/temp/cutinTemp.script"
log_file = project_root / "cutin/temp/simulation_log.csv"
output_dir = project_root / "cutin/output"

config_path = autoware_root / "src/launcher/autoware_launch/autoware_launch/config/planning/scenario_planning/common/common.param.yaml"

EGO_OFFSET = 4.913

distances = list(range(0, 65, 5))
dx_values = [EGO_OFFSET + d for d in distances]

ve_table = {
    10: 2.778, 20: 5.556, 30: 8.333, 40: 11.111, 50: 13.889, 60: 16.67
}

lat_table = {
    1:0.1, 2:0.2, 3:0.3, 4:0.4, 5:0.5, 6:0.6, 7:0.7, 8:0.8, 9:0.9, 10:1.0, 
    11:1.1, 12:1.2, 13:1.3, 14:1.4, 15:1.5, 16:1.6, 17:1.7, 18:1.8, 19:1.9, 20:2.0, 
    21:2.1, 22:2.2, 23:2.3, 24:2.4, 25:2.5, 26:2.6, 27:2.7, 28:2.8, 29:2.9, 30:3.0
}

#Overwrite the temp script
def generate_script(dx, ve, lat):
    if ve <= 8.333:
        return f'''

        spawnPos = "TrafficLane.112";
        goal = "TrafficLane.111" at 180;
        dx = {dx};
        npcspeed = {ve};
        lat = {lat};
        route1 = [
            "TrafficLane.112" max-velocity(npcspeed),
            cut-in(_, npcspeed, lat, dx),
            "TrafficLane.111" max-velocity(npcspeed)
        ];

        npc1 = NPC("hatchback", _, goal, route1, [acceleration(20)]);

        ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos left 0, "TrafficLane.111" at 130, [max-velocity(npcspeed)]);

        run("Shinjuku", ego, [npc1], [saving-timeout(70)]);

        '''
    else:
        return f'''

        spawnPos = "TrafficLane.112";
        goal = "TrafficLane.281" at 25;
        dx = {dx};
        npcspeed = {ve};
        lat = {lat};
        route1 = [
            "TrafficLane.112" max-velocity(npcspeed),
            cut-in(_, npcspeed, lat, dx),
            "TrafficLane.111" max-velocity(npcspeed),
            "TrafficLane.113" max-velocity(npcspeed),
            "TrafficLane.277" max-velocity(npcspeed),
            "TrafficLane.121" max-velocity(npcspeed),
            "TrafficLane.281" max-velocity(npcspeed)
        ];

        npc1 = NPC("hatchback", _, goal, route1, [acceleration(20)]);

        ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos left 0, "TrafficLane.281" at 3, [max-velocity(npcspeed)]);

        run("Shinjuku", ego, [npc1], [saving-timeout(70)]);

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
    #dist = dx
    tag = f"cutin{dist}-{v_kmh}-{lat_label}"
    if tag not in completed:
        run_queue.append((dx, ve, v_kmh, lat_label, lat, dist, tag))

print(f"Remaining to simulate: {len(run_queue)}")

#when queue is not empty run the next one
if run_queue:
    dx, ve, v_kmh, lat_label, lat, dist, tag = run_queue[0]
    print(f"Preparing simulation: {tag}")
    script_text = generate_script(dx, ve, lat)
    config_text = generate_config(ve)
    write_script_to_config(config_text)
    write_script_to_temp(script_text)
    print(tag)  # pass tag to bash
else:
    print("All combinations simulated.")
