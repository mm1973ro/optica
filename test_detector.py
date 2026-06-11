#!/usr/bin/env python3
"""
Test script for Optica light detection without camera.
Creates synthetic frames with simulated light sources.
"""

import cv2
import numpy as np
import yaml
from optica import LightDetector, GestureInterpreter, CommandDispatcher, Command


def create_test_frame(width=640, height=480, lights_config=None):
    """
    Create a synthetic frame with simulated light sources.

    lights_config: list of dicts with keys 'x', 'y', 'radius', 'brightness'
    """
    frame = np.zeros((height, width, 3), dtype=np.uint8)

    if lights_config:
        for light in lights_config:
            x, y = light['x'], light['y']
            radius = light.get('radius', 20)
            brightness = light.get('brightness', 255)

            # Draw a bright circle
            cv2.circle(frame, (x, y), radius, (brightness, brightness, brightness), -1)

            # Add a glow effect
            glow_radius = radius * 2
            overlay = frame.copy()
            cv2.circle(overlay, (x, y), glow_radius, (brightness//2, brightness//2, brightness//2), -1)
            frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)

    return frame


def test_detection():
    """Test light detection with various scenarios."""
    print("\n" + "="*60)
    print("TEST OPTICA - Detecție și Interpretare Semnale")
    print("="*60 + "\n")

    # Load config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    detector = LightDetector(config)
    interpreter = GestureInterpreter(config)
    dispatcher = CommandDispatcher(config)

    # Test scenarios
    scenarios = [
        {
            'name': 'ÎNAINTE - Ambele lanterne sus',
            'lights': [
                {'x': 160, 'y': 100, 'radius': 25, 'brightness': 240},
                {'x': 480, 'y': 100, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.FORWARD
        },
        {
            'name': 'ÎNAPOI - Ambele lanterne jos',
            'lights': [
                {'x': 160, 'y': 380, 'radius': 25, 'brightness': 240},
                {'x': 480, 'y': 380, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.BACKWARD
        },
        {
            'name': 'VIRAJ STÂNGA - Stânga sus, dreapta jos',
            'lights': [
                {'x': 160, 'y': 100, 'radius': 25, 'brightness': 240},
                {'x': 480, 'y': 380, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.LEFT
        },
        {
            'name': 'VIRAJ DREAPTA - Dreapta sus, stânga jos',
            'lights': [
                {'x': 160, 'y': 380, 'radius': 25, 'brightness': 240},
                {'x': 480, 'y': 100, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.RIGHT
        },
        {
            'name': 'STOP - Ambele centru',
            'lights': [
                {'x': 160, 'y': 240, 'radius': 25, 'brightness': 240},
                {'x': 480, 'y': 240, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.STOP
        },
        {
            'name': 'STOP - O singură lanternă',
            'lights': [
                {'x': 320, 'y': 240, 'radius': 25, 'brightness': 240},
            ],
            'expected': Command.STOP
        },
    ]

    results = []
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n[Test {i}/{len(scenarios)}] {scenario['name']}")
        print("-" * 60)

        # Create test frame
        frame = create_test_frame(640, 480, scenario['lights'])

        # Detect lights
        lights = detector.detect(frame)
        print(f"  Detectat: {len(lights)} surse de lumină")

        for j, light in enumerate(lights, 1):
            print(f"    Lumină {j}: poziție={light.position}, "
                  f"side={light.side}, brightness={light.brightness:.1f}")

        # Interpret command
        command, confidence = interpreter.interpret(lights)
        print(f"  Comandă: {command.value}")
        print(f"  Încredere: {confidence*100:.1f}%")

        # Check result
        passed = command == scenario['expected']
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  Status: {status}")

        results.append({
            'scenario': scenario['name'],
            'expected': scenario['expected'].value,
            'actual': command.value,
            'passed': passed,
            'confidence': confidence
        })

        # Display frame
        cv2.imshow(f"Test: {scenario['name']}", frame)
        cv2.waitKey(1000)  # Show for 1 second

    cv2.destroyAllWindows()

    # Summary
    print("\n" + "="*60)
    print("REZULTATE FINALE")
    print("="*60)

    passed_tests = sum(1 for r in results if r['passed'])
    total_tests = len(results)

    print(f"\nTeste reușite: {passed_tests}/{total_tests}")
    print(f"Rată de succes: {passed_tests/total_tests*100:.1f}%\n")

    for i, result in enumerate(results, 1):
        status = "✓" if result['passed'] else "✗"
        print(f"{status} Test {i}: {result['scenario']}")
        if not result['passed']:
            print(f"    Așteptat: {result['expected']}")
            print(f"    Primit: {result['actual']}")

    print()


def test_circular_motion():
    """Test circular motion detection."""
    print("\n" + "="*60)
    print("TEST MIȘCARE CIRCULARĂ")
    print("="*60 + "\n")

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    detector = LightDetector(config)
    interpreter = GestureInterpreter(config)

    # Simulate circular motion
    radius = 80
    center = (320, 240)
    num_frames = 20

    print("Simulez mișcare circulară...")

    for i in range(num_frames):
        angle = (i / num_frames) * 2 * np.pi

        # Two lights moving in circle
        lights_config = [
            {
                'x': int(center[0] - radius + radius * np.cos(angle)),
                'y': int(center[1] + radius * np.sin(angle)),
                'radius': 20,
                'brightness': 240
            },
            {
                'x': int(center[0] + radius + radius * np.cos(angle)),
                'y': int(center[1] + radius * np.sin(angle)),
                'radius': 20,
                'brightness': 240
            }
        ]

        frame = create_test_frame(640, 480, lights_config)
        lights = detector.detect(frame)
        command, confidence = interpreter.interpret(lights)

        # Show progress
        cv2.imshow("Test Mișcare Circulară", frame)
        cv2.waitKey(100)

        print(f"  Frame {i+1}/{num_frames}: {command.value} (încredere: {confidence*100:.1f}%)")

    cv2.destroyAllWindows()

    if command == Command.ROTATE_360:
        print("\n✓ Mișcare circulară detectată cu succes!")
    else:
        print(f"\n✗ Așteptam ROTIRE 360, am primit {command.value}")


def main():
    """Run all tests."""
    try:
        print("\nOptica - Suite de Teste")
        print("\nApasă orice tastă pentru a continua prin teste...")

        test_detection()
        print("\nTest detecție completat. Apasă ENTER pentru test mișcare circulară...")
        input()

        test_circular_motion()

        print("\n" + "="*60)
        print("TOATE TESTELE COMPLETE")
        print("="*60 + "\n")

    except KeyboardInterrupt:
        print("\n\nÎntrerupt de utilizator.")
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"\nEroare în timpul testelor: {e}")
        raise


if __name__ == '__main__':
    main()
