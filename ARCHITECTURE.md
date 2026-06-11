# Arhitectura Sistemului Optica

## Overview

Optica este un sistem modular de detecție și interpretare a semnalelor luminoase, proiectat pentru controlul unei platforme mobile prin gesturi vizuale.

## Diagrama Componentelor

```
┌─────────────────────────────────────────────────────────────┐
│                      OpticaSystem                           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Main Processing Loop                   │   │
│  │  • Capture frame                                    │   │
│  │  • Detect lights                                    │   │
│  │  • Interpret gestures                               │   │
│  │  • Dispatch commands                                │   │
│  │  • Display overlay                                  │   │
│  │  • FPS control                                      │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
           │                │               │
           ▼                ▼               ▼
    ┌─────────────┐  ┌──────────────┐  ┌──────────────┐
    │   Light     │  │   Gesture    │  │   Command    │
    │  Detector   │  │ Interpreter  │  │  Dispatcher  │
    └─────────────┘  └──────────────┘  └──────────────┘
```

## Componente Detaliate

### 1. LightDetector
**Responsabilitate**: Procesare imagine și detecție surse luminoase

**Pipeline de procesare**:
```
Frame RGB → Grayscale → Gaussian Blur → Threshold → Find Contours
                                                           ↓
                        Filter by area ← Calculate moments ←
                                ↓
                        Sort by brightness
                                ↓
                        Return top 2 lights
```

**Parametri**:
- `brightness_threshold`: Prag minim luminozitate (default: 200)
- `min_area` / `max_area`: Limite dimensiune contur
- `blur_kernel`: Dimensiune kernel blur Gaussian

**Output**: `List[LightSource]` - max 2 surse, sortate după luminozitate

### 2. LightSource (Data Class)
**Atribute**:
```python
@dataclass
class LightSource:
    position: Tuple[int, int]  # (x, y) în frame
    area: float                # Aria conturului
    brightness: float          # Luminozitate medie
    side: str                  # 'left' sau 'right'
    history: deque             # Ultimele 10 poziții
```

**Metode**:
- `update_history()`: Adaugă poziția curentă în istoric
- `get_vertical_position()`: Returnează 'up', 'down', sau 'center'
- `is_moving_circular()`: Detectează mișcare circulară

### 3. GestureInterpreter
**Responsabilitate**: Mapare poziții → comenzi

**Algoritm de interpretare**:
```
Input: List[LightSource]
  │
  ├─ Check: len(lights) < 2?
  │    └─ Yes → STOP (confidence 0.5)
  │
  ├─ Update history pentru fiecare light
  │
  ├─ Check: Circular motion?
  │    └─ Yes → ROTATE_360 (confidence 0.95)
  │
  ├─ Separate: left_lights și right_lights
  │
  ├─ Check: Ambele părți au lights?
  │    └─ No → STOP (confidence 0.6)
  │
  ├─ Get brightest from each side
  │
  ├─ Determine vertical positions (up/down/center)
  │
  ├─ Calculate confidence (bazat pe brightness)
  │
  └─ Map positions to command:
       • left=up, right=up → FORWARD
       • left=down, right=down → BACKWARD
       • left=up, right=down → LEFT
       • left=down, right=up → RIGHT
       • left=center, right=center → STOP
       • else → UNKNOWN
```

**Parametri**:
- `position_threshold`: Prag poziție verticală (default: 0.3)
- `movement_sensitivity`: Sensibilitate detectare mișcare
- `circular_motion_threshold`: Puncte minime pentru cerc (default: 8)

### 4. CommandDispatcher
**Responsabilitate**: Trimitere comenzi către sistem output

**Current implementation**: Terminal output
**Extensible pentru**:
- Serial (Arduino, ESP32)
- GPIO (Raspberry Pi)
- ROS (Robot Operating System)
- Network (UDP/TCP)

**Features**:
- Detectare schimbare comandă
- Contorizare comenzi
- State tracking

### 5. OpticaSystem (Orchestrator)
**Responsabilitate**: Integrare și coordonare

**Workflow**:
```
Initialization
  │
  ├─ Load config.yaml
  ├─ Create LightDetector
  ├─ Create GestureInterpreter
  ├─ Create CommandDispatcher
  └─ Setup camera (OpenCV VideoCapture)

Main Loop (run())
  │
  └─ while running:
       ├─ Capture frame
       ├─ Detect lights → LightDetector
       ├─ Interpret → GestureInterpreter
       ├─ Dispatch → CommandDispatcher
       ├─ Draw overlay (if display enabled)
       ├─ Show frame (if display enabled)
       ├─ Handle keyboard input
       └─ FPS control (sleep if needed)

Cleanup
  │
  ├─ Release camera
  └─ Destroy windows
```

## Data Flow

```
Camera Frame (640x480 RGB)
    ↓
[LightDetector]
    ↓
LightSource objects [x2]
{pos: (160,100), side: 'left', brightness: 240}
{pos: (480,100), side: 'right', brightness: 235}
    ↓
[GestureInterpreter]
    ↓
(Command.FORWARD, confidence: 0.93)
    ↓
[CommandDispatcher]
    ↓
Terminal: "COMANDĂ: ÎNAINTE | Încredere: 93%"
    ↓
(Future) → Serial/GPIO/ROS
```

## Extensibilitate

### Adding New Commands

1. Adaugă în enum `Command`:
```python
class Command(Enum):
    NEW_COMMAND = "COMANDĂ NOUĂ"
```

2. Adaugă logică în `GestureInterpreter.interpret()`:
```python
if left_pos == 'condition' and right_pos == 'condition':
    return Command.NEW_COMMAND, confidence
```

### Hardware Integration

**Serial Example**:
```python
import serial

class CommandDispatcher:
    def __init__(self, config: dict):
        self.serial = serial.Serial('/dev/ttyUSB0', 9600)

    def dispatch(self, command: Command, confidence: float):
        message = f"{command.name},{int(confidence*100)}\n"
        self.serial.write(message.encode())
```

**GPIO Example** (Raspberry Pi):
```python
import RPi.GPIO as GPIO

class CommandDispatcher:
    def __init__(self, config: dict):
        GPIO.setmode(GPIO.BCM)
        self.pins = {
            'forward': 17,
            'backward': 27,
            'left': 22,
            'right': 23
        }
        for pin in self.pins.values():
            GPIO.setup(pin, GPIO.OUT)

    def dispatch(self, command: Command, confidence: float):
        # Reset all pins
        for pin in self.pins.values():
            GPIO.output(pin, GPIO.LOW)

        # Activate appropriate pin
        if command == Command.FORWARD:
            GPIO.output(self.pins['forward'], GPIO.HIGH)
        # ... etc
```

## Performance Considerations

### Optimizare FPS

1. **Reduce Resolution**: 320x240 în loc de 640x480
2. **ROI (Region of Interest)**: Procesează doar zona relevantă
3. **Adjust blur_kernel**: Kernel mai mare = procesare mai rapidă, dar precizie redusă
4. **Disable Display**: `--no-video` pentru rulare headless

### Memory Usage

- `LightSource.history`: deque cu maxlen=10 (auto-cleanup)
- Frame-uri: Procesate și eliberate imediat
- Config: Loaded o singură dată

### Real-time Guarantees

- Target FPS: 30 (configurable)
- Sleep compensation pentru frame time stabil
- No blocking operations în main loop

## Testing Strategy

### Unit Tests (test_detector.py)

1. **Synthetic Frame Generation**: Creează frame-uri cu light sources simulate
2. **Scenario Testing**: Test fiecare comandă separat
3. **Motion Testing**: Test mișcare circulară cu multiple frame-uri
4. **Confidence Validation**: Verifică că confidence scores sunt rezonabili

### Integration Testing

- Camera real + lanterne reale
- Verifică latency end-to-end
- Test în condiții variabile de iluminare

## Configuration

Toate parametrii sunt centralizați în `config.yaml`:

```yaml
detection:      # LightDetector parameters
camera:         # Camera settings
roi:            # Region of Interest
gesture:        # GestureInterpreter parameters
display:        # UI settings
```

Suprascrierea via CLI:
```bash
python optica.py --threshold 180  # Override brightness_threshold
python optica.py --no-video       # Override display.show_video
```

## Future Enhancements

### Possible Improvements

1. **Multi-camera Support**: Stereo vision pentru distanță
2. **Color Detection**: Detectează lanterne colorate pentru comenzi extra
3. **Machine Learning**: CNN pentru clasificare gesture mai robustă
4. **Kalman Filtering**: Smooth light tracking
5. **IMU Integration**: Combine visual + inertial pentru robustețe
6. **Auto-calibration**: Ajustare automată threshold bazat pe ambient light
7. **Record & Replay**: Save gesture sequences pentru training
8. **Web Interface**: Control și monitoring remote via browser

### Architecture for ML Integration

```
┌─────────────────────────────────────────┐
│  Classical CV (current)                 │
│  + ML Model (future)                    │
│                                         │
│  ┌─────────────┐    ┌──────────────┐  │
│  │  Classical  │    │   ML Model   │  │
│  │  Pipeline   │    │  (CNN/LSTM)  │  │
│  └──────┬──────┘    └──────┬───────┘  │
│         │                  │           │
│         └────────┬─────────┘           │
│                  │                     │
│          ┌───────▼────────┐            │
│          │   Fusion       │            │
│          │  (Ensemble)    │            │
│          └───────┬────────┘            │
│                  │                     │
│           Final Command                │
└─────────────────────────────────────────┘
```

## Diagnoză și Debug

### Debug Mode
Adaugă verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling
```bash
python -m cProfile -o profile.stats optica.py
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumtime'); p.print_stats(20)"
```

### Visual Debugging
- Bounding boxes: Verde = stânga, Galben = dreapta
- Trajectory lines: Arată istoricul mișcării
- Confidence score: Real-time în UI
- FPS counter: Performance monitoring

---

**Note**: Această arhitectură este proiectată pentru extensibilitate și maintainability. Fiecare componentă poate fi înlocuită sau extinsă independent.
