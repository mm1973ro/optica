#!/usr/bin/env python3
"""
Optica - Light Signal Detection and Gesture Recognition System
Detects flashlight signals and interprets them as movement commands.
"""

import cv2
import numpy as np
import yaml
import argparse
import time
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum


class Command(Enum):
    """Movement commands for the platform."""
    FORWARD = "ÎNAINTE"
    BACKWARD = "ÎNAPOI"
    LEFT = "VIRAJ STÂNGA"
    RIGHT = "VIRAJ DREAPTA"
    STOP = "STOP"
    UNKNOWN = "NECUNOSCUT"


@dataclass
class LightSource:
    """Represents a detected light source."""
    position: Tuple[int, int]  # (x, y)
    area: float
    brightness: float
    side: str  # 'left' or 'right'

    def get_vertical_position(self, frame_height: int, threshold: float) -> str:
        """Determine if light is in upper or lower part of frame."""
        y = self.position[1]
        if y < frame_height * threshold:
            return 'up'
        elif y > frame_height * (1 - threshold):
            return 'down'
        return 'center'


class LightDetector:
    """Detects light sources in video frames."""

    def __init__(self, config: dict):
        self.config = config['detection']
        self.roi_config = config['roi']
        self.brightness_threshold = self.config['brightness_threshold']
        self.min_area = self.config['min_area']
        self.max_area = self.config['max_area']
        self.blur_kernel = self.config['blur_kernel']

    def detect(self, frame: np.ndarray) -> List[LightSource]:
        """
        Detect bright light sources in the frame.
        Returns list of LightSource objects.
        """
        # Apply ROI if enabled
        if self.roi_config['enabled']:
            x, y, w, h = (self.roi_config['x'], self.roi_config['y'],
                         self.roi_config['width'], self.roi_config['height'])
            roi_frame = frame[y:y+h, x:x+w]
            offset = (x, y)
        else:
            roi_frame = frame
            offset = (0, 0)

        # Convert to grayscale
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (self.blur_kernel, self.blur_kernel), 0)

        # Threshold to find bright regions
        _, thresh = cv2.threshold(blurred, self.brightness_threshold, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        lights = []
        for contour in contours:
            area = cv2.contourArea(contour)

            if self.min_area <= area <= self.max_area:
                # Calculate moments to find centroid
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"]) + offset[0]
                    cy = int(M["m01"] / M["m00"]) + offset[1]

                    # Calculate average brightness
                    mask = np.zeros(gray.shape, dtype=np.uint8)
                    cv2.drawContours(mask, [contour], -1, 255, -1)
                    brightness = cv2.mean(gray, mask=mask)[0]

                    # Determine side (left or right half of frame)
                    side = 'left' if cx < frame.shape[1] // 2 else 'right'

                    lights.append(LightSource(
                        position=(cx, cy),
                        area=area,
                        brightness=brightness,
                        side=side
                    ))

        # Sort by brightness (brightest first) and take top 2
        lights.sort(key=lambda x: x.brightness, reverse=True)
        return lights[:2]


class GestureInterpreter:
    """Interprets light positions as movement commands."""

    def __init__(self, config: dict):
        self.config = config['gesture']
        self.position_threshold = self.config['position_threshold']
        self.frame_height = config['camera']['height']
        self.frame_width = config['camera']['width']

    def interpret(self, lights: List[LightSource]) -> Tuple[Command, float]:
        """
        Interpret light positions as a command.
        Returns (Command, confidence_score).
        """
        if len(lights) < 2:
            return Command.STOP, 0.5

        # Separate left and right lights
        left_lights = [l for l in lights if l.side == 'left']
        right_lights = [l for l in lights if l.side == 'right']

        if not left_lights or not right_lights:
            # Both lights on same side - treat as STOP
            return Command.STOP, 0.6

        # Get the brightest light from each side
        left_light = left_lights[0]
        right_light = right_lights[0]

        # Determine vertical positions
        left_pos = left_light.get_vertical_position(self.frame_height, self.position_threshold)
        right_pos = right_light.get_vertical_position(self.frame_height, self.position_threshold)

        # Calculate confidence based on brightness and position clarity
        avg_brightness = (left_light.brightness + right_light.brightness) / 2
        confidence = min(avg_brightness / 255.0, 1.0)

        # Interpret command
        if left_pos == 'up' and right_pos == 'up':
            return Command.FORWARD, confidence
        elif left_pos == 'down' and right_pos == 'down':
            return Command.BACKWARD, confidence
        elif left_pos == 'up' and right_pos == 'down':
            return Command.LEFT, confidence
        elif left_pos == 'down' and right_pos == 'up':
            return Command.RIGHT, confidence
        elif left_pos == 'center' and right_pos == 'center':
            return Command.STOP, confidence * 0.8
        else:
            return Command.UNKNOWN, confidence * 0.5


class CommandDispatcher:
    """Dispatches commands to the output system."""

    def __init__(self, config: dict):
        self.last_command = None
        self.command_count = 0

    def dispatch(self, command: Command, confidence: float):
        """
        Send command to output system.
        Currently prints to terminal; can be extended for serial/GPIO/ROS.
        """
        if command != self.last_command:
            self.command_count += 1
            print(f"\n[{self.command_count}] COMANDĂ: {command.value} | Încredere: {confidence*100:.1f}%")
            self.last_command = command

    def reset(self):
        """Reset dispatcher state."""
        self.last_command = None


class OpticaSystem:
    """Main system integrating all components."""

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.detector = LightDetector(self.config)
        self.interpreter = GestureInterpreter(self.config)
        self.dispatcher = CommandDispatcher(self.config)

        # Camera setup
        self.cap = cv2.VideoCapture(self.config['camera']['device_id'])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.config['camera']['width'])
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config['camera']['height'])
        self.cap.set(cv2.CAP_PROP_FPS, self.config['camera']['fps_target'])

        self.fps_target = self.config['camera']['fps_target']
        self.mirror_mode = self.config['camera'].get('mirror_mode', True)
        self.show_video = self.config['display']['show_video']
        self.running = False

    def draw_overlay(self, frame: np.ndarray, lights: List[LightSource],
                     command: Command, confidence: float, fps: float):
        """Draw detection overlay on frame."""
        overlay = frame.copy()

        # Draw detected lights
        for i, light in enumerate(lights):
            x, y = light.position

            # Bounding box
            box_size = int(np.sqrt(light.area))
            color = (0, 255, 0) if light.side == 'left' else (0, 255, 255)
            cv2.rectangle(overlay,
                         (x - box_size, y - box_size),
                         (x + box_size, y + box_size),
                         color, 2)

            # Label
            label = f"{light.side.upper()}"
            cv2.putText(overlay, label, (x - box_size, y - box_size - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # Command display
        cmd_text = f"COMANDĂ: {command.value}"
        cv2.putText(overlay, cmd_text, (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)

        # Confidence
        if self.config['display']['confidence_display']:
            conf_text = f"Încredere: {confidence*100:.1f}%"
            cv2.putText(overlay, conf_text, (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        # FPS
        if self.config['display']['fps_display']:
            fps_text = f"FPS: {fps:.1f}"
            cv2.putText(overlay, fps_text, (10, frame.shape[0] - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        return overlay

    def run(self):
        """Main processing loop."""
        if not self.cap.isOpened():
            print("Eroare: Nu pot deschide camera!")
            return

        self.running = True
        print("\n" + "="*50)
        print("OPTICA - Sistem de Detecție Semnale Luminoase")
        print("="*50)
        print("\nAștept detectarea a două lanterne...")
        print("Apăsați 'q' pentru a ieși\n")

        frame_time = 1.0 / self.fps_target
        fps = 0

        while self.running:
            start_time = time.time()

            ret, frame = self.cap.read()
            if not ret:
                print("Eroare: Nu pot citi frame-ul!")
                break

            # Flip frame horizontally for mirror effect (left hand appears on left side)
            if self.mirror_mode:
                frame = cv2.flip(frame, 1)

            # Detect lights
            lights = self.detector.detect(frame)

            # Interpret gesture
            command, confidence = self.interpreter.interpret(lights)

            # Dispatch command
            self.dispatcher.dispatch(command, confidence)

            # Display
            if self.show_video:
                overlay = self.draw_overlay(frame, lights, command, confidence, fps)
                cv2.imshow('Optica - Detecție Semnale', overlay)

                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break

            # FPS control
            elapsed = time.time() - start_time
            sleep_time = max(0, frame_time - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

            fps = 1.0 / (time.time() - start_time)

        self.cleanup()

    def cleanup(self):
        """Release resources."""
        self.running = False
        self.cap.release()
        cv2.destroyAllWindows()
        print("\n\nSistem oprit. La revedere!")


def main():
    parser = argparse.ArgumentParser(
        description='Optica - Sistem de detecție semnale luminoase și control mișcare'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Cale către fișierul de configurare (default: config.yaml)'
    )
    parser.add_argument(
        '--threshold',
        type=int,
        help='Suprascrie pragul de luminozitate din config'
    )
    parser.add_argument(
        '--no-video',
        action='store_true',
        help='Dezactivează afișarea video (doar comenzi în terminal)'
    )

    args = parser.parse_args()

    try:
        system = OpticaSystem(args.config)

        # Override config with CLI arguments
        if args.threshold:
            system.detector.brightness_threshold = args.threshold
        if args.no_video:
            system.show_video = False

        system.run()

    except FileNotFoundError:
        print(f"Eroare: Fișierul de configurare '{args.config}' nu a fost găsit!")
    except KeyboardInterrupt:
        print("\n\nÎntrerupt de utilizator.")
    except Exception as e:
        print(f"Eroare: {e}")
        raise


if __name__ == '__main__':
    main()
