# Optica - Sistem de Detecție Semnale Luminoase

Aplicație Python de Computer Vision care detectează semnale luminoase (lanterne) printr-o cameră video și le interpretează ca comenzi de mișcare pentru o platformă cu două roți.

## Funcționalități

- **Detecție în timp real** a două surse de lumină distincte
- **Interpretare gesture** bazată pe poziția lanternelor
- **Afișare vizuală** cu overlay și tracking
- **Sistem de comenzi** pregătit pentru extindere hardware

## Comenzi Suportate

| Poziție Lanterne | Comandă |
|-----------------|---------|
| Ambele SUS | ⬆️ ÎNAINTE |
| Ambele JOS | ⬇️ ÎNAPOI |
| Stânga SUS, Dreapta JOS | ⬅️ VIRAJ STÂNGA |
| Dreapta SUS, Stânga JOS | ➡️ VIRAJ DREAPTA |
| Ambele CENTRU | ⏸️ STOP |

## Instalare

```bash
# Instalare dependențe
pip install -r requirements.txt
```

## Utilizare

### Mod Normal (cu video)
```bash
python optica.py
```

### Configurare Personalizată
```bash
# Folosește un fișier de configurare diferit
python optica.py --config my_config.yaml

# Suprascrie pragul de luminozitate
python optica.py --threshold 180

# Mod terminal (fără video)
python optica.py --no-video
```

## Configurare

Editează `config.yaml` pentru a ajusta parametrii:

### Detecție
- `brightness_threshold`: Pragul minim de luminozitate (0-255)
- `min_area` / `max_area`: Limita dimensiunii conturului
- `blur_kernel`: Dimensiunea kernel-ului de blur

### Cameră
- `device_id`: ID-ul camerei (0 pentru camera default)
- `width` / `height`: Rezoluția
- `fps_target`: FPS țintă

### Gesture
- `position_threshold`: Pragul de poziție verticală (0-1)
- `movement_sensitivity`: Sensibilitatea detectării mișcării
- `circular_motion_threshold`: Pragul pentru detectarea mișcării circulare

### ROI (Region of Interest)
- `enabled`: Activează restricția zonei de interes
- `x`, `y`, `width`, `height`: Coordonatele ROI

## Arhitectură

```
optica.py
├── LightDetector      # Procesare imagine, detecție surse luminoase
├── GestureInterpreter # Mapare poziții → comenzi
├── CommandDispatcher  # Trimitere comenzi (terminal/hardware)
└── OpticaSystem      # Integrare componente și loop principal
```

### Clase Principale

#### `LightDetector`
- Procesează frame-uri video cu OpenCV
- Detectează surse luminoase bazat pe luminozitate și arie
- Filtrează și sortează detectările

#### `GestureInterpreter`
- Analizează poziția relativă a lanternelor
- Detectează mișcare circulară
- Calculează încrederea detecției

#### `CommandDispatcher`
- Afișează comenzile în terminal
- Pregătit pentru extindere: serial, GPIO, ROS

#### `OpticaSystem`
- Coordonează toate componentele
- Gestionează loop-ul de procesare
- Afișează overlay-ul video

## Extindere Hardware

Pentru a conecta sistemul la hardware (motoare, platformă robotică):

1. **Serial/Arduino**:
```python
import serial
ser = serial.Serial('/dev/ttyUSB0', 9600)

def dispatch(self, command: Command, confidence: float):
    ser.write(f"{command.name}\n".encode())
```

2. **GPIO (Raspberry Pi)**:
```python
import RPi.GPIO as GPIO

def dispatch(self, command: Command, confidence: float):
    if command == Command.FORWARD:
        GPIO.output(MOTOR_LEFT_PIN, GPIO.HIGH)
        GPIO.output(MOTOR_RIGHT_PIN, GPIO.HIGH)
```

3. **ROS (Robot Operating System)**:
```python
import rospy
from geometry_msgs.msg import Twist

pub = rospy.Publisher('/cmd_vel', Twist, queue_size=10)

def dispatch(self, command: Command, confidence: float):
    twist = Twist()
    if command == Command.FORWARD:
        twist.linear.x = 0.5
    pub.publish(twist)
```

## Troubleshooting

### Camera nu se deschide
- Verifică `device_id` în config
- Testează cu: `ls /dev/video*` (Linux) sau verifică System Preferences (macOS)

### Detecții false
- Crește `brightness_threshold`
- Ajustează `min_area` și `max_area`
- Activează ROI pentru a limita zona de căutare

### FPS scăzut
- Reduce rezoluția în config
- Crește `blur_kernel` pentru procesare mai rapidă
- Dezactivează display-ul cu `--no-video`

## Licență

MIT License

## Contact

Pentru probleme sau sugestii, deschide un issue pe repository.
