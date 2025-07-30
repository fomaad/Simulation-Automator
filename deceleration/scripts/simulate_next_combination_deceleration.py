import os
import itertools
import shutil
from pathlib import Path

# root paths
project_root = Path("/path/to/project")
autoware_root = Path("/path/to/autoware") #eg. /home/user/autoware

# paths
script_template_path = project_root / "deceleration/temp/decelerationTemp.script"
log_file = project_root / "deceleration/temp/simulation_log.csv"
output_dir = project_root / "deceleration/output"

config_path = autoware_root / "src/launcher/autoware_launch/autoware_launch/config/planning/scenario_planning/common/common.param.yaml"

EGO_OFFSET = 4.913

distances = list(range(0, 65, 5))
dx_values = [EGO_OFFSET + d for d in distances]

ve_table = {
    10: 2.778, 20: 5.556, 30: 8.333, 40: 11.111, 50: 13.889, 60: 16.67
}

deo_table = {
    1.000: 1000, 3.447: 3447,
    3.937: 3937, 6.384: 6384,
    6.873: 6873, 9.810: 9810
}

#Overwrite the temp script
def generate_script(dx, ve, vo, deo):
    if ve==2.778 or ve ==5.556:
        return f'''spawnPos = "TrafficLane.111" at 2;
    goal = "TrafficLane.111" at 90;

    dx = {dx};
    ve = {ve}; 
    vo = {vo};
    deo = {deo};

    route1 = [
        "TrafficLane.111" max-velocity(vo)
    ];

    npc1 = NPC("smallcar", spawnPos forward dx, goal, route1,
        [acceleration(3), 
        deceleration(deo), 
        aggressive-driving,
        delay-move-until-ego-engaged(1)]);

    npc2 = NPC("smallcar", _, [delay-spawn(_)]);

    ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos, "TrafficLane.111" at 120, [max-velocity(ve)]);

    run("Shinjuku", ego, [npc1,npc2], [saving-timeout(60)]);
    '''
    elif ve == 8.333:
        return f'''spawnPos = "TrafficLane.111" at 2;
    goal = "TrafficLane.111" at 160;

    dx = {dx};
    ve = {ve}; 
    vo = {vo};
    deo = {deo};

    route1 = [
        "TrafficLane.111" max-velocity(vo)
    ];

    npc1 = NPC("smallcar", spawnPos forward dx, goal, route1,
        [acceleration(3), 
        deceleration(deo), 
        aggressive-driving,
        delay-move-until-ego-engaged(1)]);

    npc2 = NPC("smallcar", _, [delay-spawn(_)]);

    ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos, "TrafficLane.111" at 180, [max-velocity(ve)]);

    run("Shinjuku", ego, [npc1,npc2], [saving-timeout(60)]);
    '''
    else:
        return f'''spawnPos = "TrafficLane.111" at 2;
    goal = "TrafficLane.111" at 200;

    dx = {dx};
    ve = {ve}; 
    vo = {vo};
    deo = {deo};

    route1 = [
        "TrafficLane.111" max-velocity(vo)
    ];

    npc1 = NPC("smallcar", spawnPos forward dx, goal, route1,
        [acceleration(3), 
        deceleration(deo), 
        aggressive-driving,
        delay-move-until-ego-engaged(1)]);

    npc2 = NPC("smallcar", _, [delay-spawn(_)]);

    ego = Ego("Lexus RX450h 2015 Sample Sensor", spawnPos, "TrafficLane.111" at 220, [max-velocity(ve)]);

    run("Shinjuku", ego, [npc1,npc2], [saving-timeout(60)]);
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

def rename_output_files(dist, v_kmh, deo_label):
    base_name = f"deceleration{dist}-{v_kmh}-{deo_label}-lidarCam"
    for ext in [".yaml", ".maude"]:
        src = os.path.join(output_dir, f"Temp.out{ext}")
        dst = os.path.join(output_dir, f"{base_name}{ext}")
        if os.path.exists(src):
            shutil.move(src, dst)
        else:
            print(f"⚠ Warning: Missing expected output file {src}")

combinations = list(itertools.product(dx_values, ve_table.items(), deo_table.items()))
print(f"Total combinations: {len(combinations)}")

# Load already simulated tags
completed = set()
if os.path.exists(log_file):
    with open(log_file, "r") as log:
        completed = {line.strip() for line in log if line.strip()}

# Determine next simulation
run_queue = []
for dx, (v_kmh, ve), (deo, deo_label) in combinations:
    dist = round(dx - EGO_OFFSET)
    tag = f"deceleration{dist}-{v_kmh}-{deo_label}-lidarCam"
    if tag not in completed:
        run_queue.append((dx, ve, v_kmh, deo, deo_label, dist, tag))

print(f"Remaining to simulate: {len(run_queue)}")

#when queue is not empty run the next one
if run_queue:
    dx, ve, v_kmh, deo, deo_label, dist, tag = run_queue[0]
    print(f"Preparing simulation: {tag}")
    script_text = generate_script(dx, ve, ve, deo)
    config_text = generate_config(ve)
    write_script_to_config(config_text)
    write_script_to_temp(script_text)
    print(tag)  # pass tag to bash
else:
    print("All combinations simulated.")
