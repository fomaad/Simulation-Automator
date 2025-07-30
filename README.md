# Simulation-Automator

This project automates the simulation workflow for AWSIM/Unity with Autoware by:
- Automatically launching Unity and Autoware,
- Applying different scenario variables based on the JAMA framework,
- Recording ROS images and screen output,
- Running all defined parameter combinations in a loop without human interaction.

The goal is to simulate various parameter changes under the same scenario setup (e.g., cut-in, deceleration, etc.). Each scenario directory handles its specific simulation setup and output collection.

> **Note**:  
> This project was developed by **Tanadol Chuntarasupt** during an internship at **JAIST in 2025**. It was designed specifically for use on Tanadol’s device and is not guaranteed to work elsewhere without modification.  
> Before running anything, **please inspect and modify all parts commented as `'CONFIG THIS'`** to suit your local environment and setup.

---

## Directory Structure and Key Scripts

```
./cutin/
│
├── /output/                       # Stores simulation outputs (.yaml, .maude)
├── /recordings/
│   ├── /ROSImages/                # Captured videos from ROSImageRecorder
│   └── /ScreenRecordings/         # Screen capture output
├── /scripts/
│   ├── ROSImageRecorder.py        # Records images from ROS topics into video
│   └── simulate_next_combination_cutin.py  # Overwrites Unity and Autoware config for next param set
├── /temp/
│   ├── cutinTemp.script           # Unity reads this script per simulation run
│   └── simulation_log.csv         # Tracks simulation progress and current state
├── simulate_cutin.sh              # Main automation script: manages window focus, runs recorder, etc.
└── cutinNote.txt                  # Scenario-specific notes and logs
```

```
./deceleration/
├── (similar structure to ./cutin/)
```

```
./cutout/  ← ⚠ Not usable yet (under development)
├── (same structure as above)
```

---

## How to Run (Step-by-Step)

1. **Start Unity manually** with a temporary script and appropriate output directory.  
   On your terminal, on this project path:

   ```bash
   ~/Unity/Hub/Editor/2022.3.57f1/Editor/Unity -projectPath . -script /path/to/scenarioTemp.script -output /path/to/output/Temp.out
   ```

2. **Configure paths** in both:
   - The bash script (`simulate_*.sh`)
   - The Python simulation script (`simulate_next_combination_*.py`)

3. **Edit the parameter combinations** you want to test in the Python script.

4. **Run the automation script**:
   ```bash
   ./simulate_cutin.sh
   ```

---
## Dependencies

You'll need Python 3.x and the following packages (can be installed via pip):

```bash
pip install opencv-python cv_bridge rclpy
```

Note: ROS2 and Autoware should be properly installed and sourced in your environment.

---

### Python Built-in Modules Used

- os  
- sys  
- shutil  
- argparse  
- itertools  
- signal  
- time  

---

