"""
Advanced float fishing detection demonstration
Run this to test float and bite detection on your screen
"""
import cv2
import mss
import numpy as np
from vision.float_detectors import HybridFloatDetector


def main():
    print("Float Detection Demo - Press ESC to exit")
    print("Configure detection_region in GUI before running")
    print()
    
    detector = HybridFloatDetector(target_color="red")
    sct = mss.mss()
    
    # Get primary monitor
    monitor = sct.monitors[1]
    
    frame_count = 0
    bite_count = 0
    
    while True:
        # Capture screen
        screenshot = sct.grab(monitor)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
        
        # Resize for display (optional - for performance)
        display_frame = cv2.resize(frame, (960, 540))
        
        # Detect float
        float_info = detector.detect_float(display_frame)
        
        # Draw detection region (example: center area)
        region_x, region_y = 400, 200
        region_w, region_h = 400, 300
        cv2.rectangle(display_frame, (region_x, region_y), 
                     (region_x + region_w, region_y + region_h), 
                     (0, 255, 0), 2)
        cv2.putText(display_frame, "Detection Region", (region_x, region_y - 10),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        # Draw float info
        if float_info:
            pos = float_info.get('position')
            radius = float_info.get('radius', 10)
            confidence = float_info.get('confidence', 0)
            
            cv2.circle(display_frame, pos, int(radius), (0, 255, 0), 2)
            cv2.circle(display_frame, pos, 3, (0, 0, 255), -1)
            cv2.putText(display_frame, f"Float at {pos}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            cv2.putText(display_frame, f"Confidence: {confidence:.2f}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Detect bite
            bite_result = detector.detect_bite(display_frame, sensitivity=0.65)
            if bite_result['detected']:
                bite_count += 1
                cv2.putText(display_frame, "BITE DETECTED!", (10, 90),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)
                cv2.putText(display_frame, f"Methods: {bite_result['methods']}", (10, 120),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Frame info
        frame_count += 1
        cv2.putText(display_frame, f"Frame: {frame_count} | Bites: {bite_count}", (10, 520),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Display
        cv2.imshow("Float Detection Demo", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            break
    
    cv2.destroyAllWindows()
    print(f"Demo ended. Total frames: {frame_count}, Bites detected: {bite_count}")


if __name__ == "__main__":
    main()
