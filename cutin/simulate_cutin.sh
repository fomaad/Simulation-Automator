#!/bin/bash

# root paths
PROJECT_ROOT="/path/to/project"
AUTOWARE_DIR="/path/to/autoware" #eg. /home/user/autoware
MAP_ROOT="/path/to/autoware_map" #eg. /home/user/autoware_map

PROJECT="$PROJECT_ROOT/cutin"

# paths
PYTHON_SCRIPT= "$PROJECT/scripts/simulate_next_combination_cutin.py"
TEMP_SCRIPT= "$PROJECT/temp/cutinTemp.script"
OUTPUT_DIR= "$PROJECT/output"
MAP_PATH= "$MAP_ROOT/nishishinjuku_autoware_map"
RECORDING_DIR= "$PROJECT/recordings/ScreenRecordings"
LOG_FILE= "$PROJECT/temp/simulation_log.csv"

ROS_SCRIPT="$PROJECT/scripts/ROSImageRecorder.py"
ROS_VIDEO_DIR="$PROJECT/recordings/ROSImages"
ROS_TEMP_VIDEO="$ROS_VIDEO_DIR/TempRec.mp4"
ROS_FINAL_VIDEO="$ROS_VIDEO_DIR/${OUTNAME}.mp4"

#to explicitly define winid
: '
 AUTOWARE_WINID="90178038"
 UNITY_WINID="71303606"
'
#main loop to run the main python script
while true; do
    echo "Preparing next simulation..."
    python3 "$PYTHON_SCRIPT"

    DX_LINE=$(grep -oP 'dx = \K[0-9.]+' "$TEMP_SCRIPT")
    VE_LINE=$(grep -oP 'npcspeed = \K[0-9.]+' "$TEMP_SCRIPT")
    LAT_LINE=$(grep -oP 'lat = \K[0-9.]+' "$TEMP_SCRIPT")

    if [[ -z "$DX_LINE" || -z "$VE_LINE" || -z "$LAT_LINE" ]]; then
        echo "Failed to extract dx, ve, or deo. Skipping..."
        continue
    fi

    DIST=$(awk "BEGIN { printf \"%.0f\", $DX_LINE - 4.913 }")
    VE_KMH=$(awk "BEGIN { printf \"%.0f\", $VE_LINE * 3.6 }")
    LAT_TAG=$(awk "BEGIN { printf \"%.0f\", $LAT_LINE * 10 }")

    OUTNAME="cutin${DIST}-${VE_KMH}-${LAT_TAG}"
    echo "Output will be saved as: ${OUTNAME}.yaml and ${OUTNAME}.maude"

    echo "Launching Autoware..."
    gnome-terminal -- bash -c "cd $AUTOWARE_DIR && source install/setup.bash && ros2 launch autoware_launch e2e_simulator.launch.xml vehicle_model:=awsim_labs_vehicle sensor_model:=awsim_labs_sensor_kit map_path:=$MAP_PATH perception_mode:=lidar launch_vehicle_interface:=true; exec bash"

#fetch winid for unity and autoware
while true; do
    AUTOWARE_WINID=$(xdotool search --name "autoware.rviz" 2>/dev/null | head -n 1)
    UNITY_WINID=$(xdotool search --name "Unity" 2>/dev/null | head -n 1)

    if [ -n "$AUTOWARE_WINID" ] && [ -n "$UNITY_WINID" ]; then
        echo "Found AUTOWARE_WINID: $AUTOWARE_WINID"
        echo "Found UNITY_WINID: $UNITY_WINID"
        break
    fi

    sleep 1
done

while ! xdotool getwindowname "$AUTOWARE_WINID" &>/dev/null || \
      ! xdotool getwindowname "$UNITY_WINID" &>/dev/null; do
    sleep 1
done

sleep 5

# !! CONFIG THIS TO FIT YOUR SCREEN AND NEEDS !!
#open autoware and config the app window to display what you want
xdotool windowactivate --sync $AUTOWARE_WINID 2>/dev/null
xdotool mousemove 1867 229
xdotool click 1
xdotool windowmove $AUTOWARE_WINID 0 248
xdotool windowsize $AUTOWARE_WINID 960 1043

xdotool mousemove 526 1242
xdotool click 1

xdotool mousemove 773 886
xdotool click 1

xdotool mousemove 471 792
xdotool click 1

# !! CONFIG THIS TO FIT YOUR SCREEN AND NEEDS !!
#Record screen
	RECORDING_FILE="$RECORDING_DIR/${OUTNAME}.mkv"
	ffmpeg -f x11grab -video_size 1920x1080 -i :1.0+0,211 "$RECORDING_FILE" > /dev/null 2>&1 &
FFMPEG_PID=$!

#ROS Images recording
: '
 source /opt/ros/humble/setup.bash
 	python3 "$ROS_SCRIPT" --output TempRec & 
 ROS_RECORDING_PID=$!
 	echo $ROS_RECORDING_PID
'
	echo "Started screen recording: $RECORDING_FILE"

# !! CONFIG THIS TO FIT YOUR SCREEN AND NEEDS !!
#play unity
xdotool windowactivate --sync $UNITY_WINID 2>/dev/null
xdotool mousemove 1410 290
xdotool click 1

xdotool mousemove 3310 701

#Wait until simulation finish, modify output filenames and go next
    while [[ ! -f "$OUTPUT_DIR/Temp.out.yaml" || ! -f "$OUTPUT_DIR/Temp.out.maude" ]]; do
    sleep 1  
done
	
    if [ -f "$OUTPUT_DIR/Temp.out.yaml" ] && [ -f "$OUTPUT_DIR/Temp.out.maude" ]; then
        mv "$OUTPUT_DIR/Temp.out.yaml" "$OUTPUT_DIR/${OUTNAME}.yaml"
        mv "$OUTPUT_DIR/Temp.out.maude" "$OUTPUT_DIR/${OUTNAME}.maude"
        echo "Output files renamed to $OUTNAME.*"
	echo "$OUTNAME" >> "$LOG_FILE"
	
    	echo "Closing Autoware..."
    	pkill -f "ros2 launch autoware_launch"
    	
    	kill $FFMPEG_PID
	wait $FFMPEG_PID 2>/dev/null
	echo "Stopped screen recording."
	
#for ROS recording script
: '
 	kill $ROS_RECORDING_PID
 	sleep 10
 	kill $ROS_RECORDING_PID
 	wait $ROS_RECORDING_PID 2>/dev/null
 	if [ -f "$ROS_TEMP_VIDEO" ]; then
    		mv "$ROS_VIDEO_DIR/TempRec.mp4" "$ROS_VIDEO_DIR/${OUTNAME}.mp4"
    		echo "ROS Video renamed to $ROS_FINAL_VIDEO"
	else
    		echo "ROS Video recording failed or not found!"
	fi
'
	
    	echo "Simulation for $OUTNAME complete."
    	
    else
        echo "Output files not found"
    	echo "Closing Autoware..."
    	pkill -f "ros2 launch autoware_launch"
    	rm "$RECORDING_FILE"
    	kill $FFMPEG_PID
	wait $FFMPEG_PID 2>/dev/null
	echo "Stopped screen recording."
    	echo "Simulation for $OUTNAME ERROR"
    fi

    echo "-------------------------------------------"

# !! CONFIG THIS TO FIT YOUR SCREEN AND NEEDS !!
#Stop playing unity to refetch the script
xdotool windowactivate --sync $UNITY_WINID 2>/dev/null
xdotool mousemove 1410 290
xdotool click 1

xdotool mousemove 3310 701

	sleep 10
done

