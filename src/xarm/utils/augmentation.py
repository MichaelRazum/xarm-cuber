"""
Time-based augmentation utilities for robot vision data.

This module provides functions to add temporal information to camera images,
helping robots understand sequence timing and when to stop actions.
"""

import cv2
import numpy as np
from typing import Tuple, Optional, Union


def add_progress_bar(
    image: np.ndarray, 
    elapsed_time: float,
    total_duration: float = 30.0,
    bar_height: int = 10,
    use_color_progression: bool = True,
    background_color: Tuple[int, int, int] = (100, 100, 100)
) -> np.ndarray:
    """
    Add a horizontal progress bar to the bottom of an image with color progression.
    
    Args:
        image: Input image (BGR format)
        elapsed_time: Current elapsed time in seconds
        total_duration: Total expected duration in seconds (default: 30.0)
        bar_height: Height of progress bar in pixels
        use_color_progression: If True, color changes from red to green to blue over time
        background_color: BGR color for remaining portion (default: gray)
        
    Returns:
        Image with progress bar overlay
    """
    img_copy = image.copy()
    h, w = img_copy.shape[:2]
    
    # Calculate progress
    progress = min(elapsed_time / max(total_duration, 0.1), 1.0)
    bar_width = int(w * progress)
    
    # Determine bar color
    if use_color_progression:
        # Map time to hue (0=red, 120=green, 240=blue)
        hue = int(progress * 240)
        # Create HSV color and convert to BGR
        hsv_color = np.array([[[hue, 255, 255]]], dtype=np.uint8)
        bar_color = cv2.cvtColor(hsv_color, cv2.COLOR_HSV2BGR)[0, 0]
        bar_color = tuple(map(int, bar_color))
    else:
        bar_color = (0, 255, 0)  # Default green
    
    # Draw progress bar at bottom
    cv2.rectangle(img_copy, (0, h - bar_height), (bar_width, h), bar_color, -1)
    cv2.rectangle(img_copy, (bar_width, h - bar_height), (w, h), background_color, -1)
    
    return img_copy


def add_timestamp_overlay(
    image: np.ndarray,
    elapsed_time: float,
    position: Tuple[int, int] = (15, 35),
    font_scale: float = 1.0,
    font_color: Tuple[int, int, int] = (255, 255, 255),
    background_color: Optional[Tuple[int, int, int]] = (0, 0, 0),
    precision: int = 1
) -> np.ndarray:
    """
    Add timestamp text overlay to an image.
    
    Args:
        image: Input image (BGR format)
        elapsed_time: Time in seconds to display
        position: (x, y) position for text
        font_scale: Size of the font
        font_color: BGR color for text (default: white)
        background_color: BGR color for background box (None for no background)
        precision: Number of decimal places for time display
        
    Returns:
        Image with timestamp overlay
    """
    img_copy = image.copy()
    timestamp_text = f"t: {elapsed_time:.{precision}f}s"
    
    # Calculate text size
    font = cv2.FONT_HERSHEY_SIMPLEX
    (text_w, text_h), baseline = cv2.getTextSize(timestamp_text, font, font_scale, 2)
    
    # Draw background box if specified
    if background_color is not None:
        x, y = position
        cv2.rectangle(
            img_copy, 
            (x - 5, y - text_h - 5), 
            (x + text_w + 5, y + baseline + 5), 
            background_color, 
            -1
        )
    
    # Draw text
    cv2.putText(img_copy, timestamp_text, position, font, font_scale, font_color, 2)
    
    return img_copy



class TimeAugmenter:
    """
    A class to manage time-based augmentation for a sequence of images.
    """
    
    def __init__(
        self,
        total_duration: float,
        fps: float = 30.0,
        use_progress_bar: bool = True,
        use_timestamp: bool = True
    ):
        """
        Initialize the time augmenter.
        
        Args:
            total_duration: Expected total duration in seconds
            fps: Frames per second of the sequence
            use_progress_bar: Whether to add progress bar with color progression
            use_timestamp: Whether to add timestamp overlay
        """
        self.total_duration = total_duration
        self.fps = fps
        self.total_frames = int(total_duration * fps)
        self.use_progress_bar = use_progress_bar
        self.use_timestamp = use_timestamp
    
    def augment_frame(
        self,
        image: np.ndarray,
        frame_number: int,
        elapsed_time: Optional[float] = None
    ) -> np.ndarray:
        """
        Apply time-based augmentation to a single frame.
        
        Args:
            image: Input image (BGR format)
            frame_number: Current frame number (0-indexed)
            elapsed_time: Elapsed time in seconds (computed from frame_number if None)
            
        Returns:
            Augmented image
        """
        if elapsed_time is None:
            elapsed_time = frame_number / self.fps
        
        augmented_image = image.copy()
        
        if self.use_progress_bar:
            augmented_image = add_progress_bar(
                augmented_image, elapsed_time, self.total_duration
            )
        
        if self.use_timestamp:
            augmented_image = add_timestamp_overlay(
                augmented_image, elapsed_time
            )
        
        
        return augmented_image
    
    def get_frame_info(self, frame_number: int) -> dict:
        """
        Get information about a frame's temporal context.
        
        Args:
            frame_number: Current frame number (0-indexed)
            
        Returns:
            Dictionary with frame information
        """
        elapsed_time = frame_number / self.fps
        progress = min(frame_number / max(self.total_frames, 1), 1.0)
        
        return {
            "frame_number": frame_number,
            "elapsed_time": elapsed_time,
            "progress": progress,
            "total_frames": self.total_frames,
            "total_duration": self.total_duration,
            "fps": self.fps
        }