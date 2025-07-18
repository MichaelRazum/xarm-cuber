#!/usr/bin/env python3
"""
Helper script to find camera devices by USB path.
"""
import subprocess
import sys

def find_webcam_by_usb_path(usb_path_substring):
    """Find camera device path by USB path substring."""
    try:
        output = subprocess.check_output("v4l2-ctl --list-devices", shell=True, text=True)
        devices = output.split('\n\n')
        for device_info in devices:
            # Each device_info block has lines like:
            # C922 Pro Stream Webcam (usb-0000:00:14.0-5.2.3):
            #    /dev/video2
            #    /dev/video3
            #    /dev/media1
            if usb_path_substring in device_info:
                # The lines after the colon are the relevant /dev/videoX lines
                lines = device_info.split('\n')
                for line in lines:
                    if "video" in line:
                        parts = line.split()
                        for part in parts:
                            if part.startswith('/dev/video'):
                                return part
        return None
    except subprocess.CalledProcessError:
        return None

def main():
    if len(sys.argv) != 3:
        print("Usage: find_cameras.py <top_usb_path> <front_usb_path>", file=sys.stderr)
        sys.exit(1)
    
    top_usb_path = sys.argv[1]
    front_usb_path = sys.argv[2]
    
    top_cam = find_webcam_by_usb_path(top_usb_path)
    front_cam = find_webcam_by_usb_path(front_usb_path)
    
    if not top_cam:
        print(f"ERROR: Top camera not found at USB path {top_usb_path}", file=sys.stderr)
        sys.exit(1)
    
    if not front_cam:
        print(f"ERROR: Front camera not found at USB path {front_usb_path}", file=sys.stderr)
        sys.exit(1)
    
    # Output camera configuration for LeRobot
    cameras_config = f'{{top: {{type: opencv, index_or_path: "{top_cam}", width: 640, height: 480, fps: 30}}, front: {{type: opencv, index_or_path: "{front_cam}", width: 640, height: 480, fps: 30}}}}'
    
    print(cameras_config)

if __name__ == "__main__":
    main()