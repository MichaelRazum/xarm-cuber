import cv2
import numpy as np
import pytest
from xarm.utils.augmentation import add_progress_bar, add_timestamp_overlay, TimeAugmenter


def create_synthetic_image() -> np.ndarray:
    """Create a synthetic test image."""
    test_image = np.zeros((480, 640, 3), dtype=np.uint8)
    test_image[:] = (50, 100, 150)  # BGR background color
    # Add visual elements
    cv2.rectangle(test_image, (100, 100), (200, 200), (255, 255, 255), -1)
    cv2.circle(test_image, (400, 300), 50, (0, 255, 0), -1)
    cv2.putText(test_image, "Test Image", (250, 400), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    return test_image


def display_image(image: np.ndarray, title: str = "Image"):
    """Display image using matplotlib if available."""
    import matplotlib.pyplot as plt

    # Convert BGR to RGB for matplotlib
    if len(image.shape) == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image

    plt.figure(figsize=(10, 8))
    plt.imshow(image_rgb)
    plt.title(title)
    plt.axis('off')
    plt.show()


@pytest.mark.parametrize("elapsed_time", [0.0, 10.0, 30.0])
def test_add_progress_bar(elapsed_time, display=False):
    """Test progress bar augmentation function."""
    # Test with synthetic image
    image = create_synthetic_image()
    
    # Apply augmentation
    augmented_image = add_progress_bar(image, elapsed_time)
    
    # Basic checks
    assert augmented_image.shape == image.shape
    assert augmented_image.dtype == image.dtype
    assert not np.array_equal(augmented_image, image)  # Should be different
    
    # Check that progress bar is at the bottom
    h, w = image.shape[:2]
    bar_region = augmented_image[h-10:h, :, :]
    original_region = image[h-10:h, :, :]
    assert not np.array_equal(bar_region, original_region)  # Bar region should be different
    
    if display:
        display_image(augmented_image, f"Progress Bar - {elapsed_time}s")


@pytest.mark.parametrize("elapsed_time", [0.0, 10.0, 30.0])
def test_add_timestamp_overlay(elapsed_time, display=False):
    """Test timestamp overlay augmentation function."""
    # Test with synthetic image
    image = create_synthetic_image()
    
    # Apply augmentation
    augmented_image = add_timestamp_overlay(image, elapsed_time)
    
    # Basic checks
    assert augmented_image.shape == image.shape
    assert augmented_image.dtype == image.dtype
    assert not np.array_equal(augmented_image, image)  # Should be different
    
    timestamp_region = augmented_image[0:50, 0:150, :]
    original_region = image[0:50, 0:150, :]
    assert not np.array_equal(timestamp_region, original_region)  # Timestamp region should be different
    
    if display:
        display_image(augmented_image, f"Timestamp - {elapsed_time}s")



@pytest.mark.parametrize("elapsed_time", [0.0, 10.0, 30.0])
def test_time_augmenter(elapsed_time, display=False):
    """Test TimeAugmenter class."""
    # Test with synthetic image
    image = create_synthetic_image()
    
    # Create augmenter
    augmenter = TimeAugmenter(total_duration=30.0, fps=30.0)
    frame_number = int(elapsed_time * 30)
    
    # Apply augmentation
    augmented_image = augmenter.augment_frame(image, frame_number, elapsed_time)
    
    # Basic checks
    assert augmented_image.shape == image.shape
    assert augmented_image.dtype == image.dtype
    assert not np.array_equal(augmented_image, image)  # Should be different
    
    # Get frame info
    frame_info = augmenter.get_frame_info(frame_number)
    assert frame_info['elapsed_time'] == elapsed_time
    assert frame_info['total_duration'] == 30.0
    
    if display:
        display_image(augmented_image, f"Combined Augmentation - {elapsed_time}s")

