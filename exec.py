import os

commands = [
    "pip install -r requirements.txt",
    "python mosquitto/broker.py",
    "cd server && python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload",
    "python main.py --source edge/assets/test2.mp4 --fps 10 --show-video --verbose --aspect-ratio 16:9 --crop-anchor center"
]

for command in commands:
    os.system(f'start cmd /k "{command}"')

#