import torch
import torch.nn as nn
from torchvision import models, transforms
import requests
import numpy as np
from tqdm import tqdm
import json
from PIL import Image
from io import BytesIO
import random
from ultralytics import YOLO

torch.device('cpu') 
print(torch.cuda.is_available()) 

# Configuration
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
BATCH_SIZE = 64  # On réduit car chaque image sera traitée objet par objet
torch.backends.cudnn.benchmark = True

# YOLOv8 (utilise le modèle léger pour rapidité plus que YOLOv5)
yolo = YOLO("yolov8n.pt")

# MobileNet
mobilenet = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
mobilenet.classifier[-1] = nn.Identity()
mobilenet = mobilenet.to(device).eval()

# Préprocessing MobileNet
preprocess = transforms.Compose([
    transforms.Resize((224, 224)),  # Adapter à la crop
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def robust_download(url, max_retries=1):
    try:
        response = requests.get(url, timeout=2)
        return Image.open(BytesIO(response.content)).convert("RGB")
    except:
        return Image.new('RGB', (224, 224), color=(
            random.randint(50, 200),
            random.randint(50, 200),
            random.randint(50, 200)
        ))

def extract_objects(image):
    results = yolo(image, device='cpu', verbose=False)

    detected = []
    for result in results:
        for box in result.boxes:
            try:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                class_id = int(box.cls[0])
                label = result.names[class_id]
                # Découpe de l'objet détecté à partir des coordonnées (bounding box) avec PIL
                cropped = image.crop((x1, y1, x2, y2))
                tensor = preprocess(cropped).unsqueeze(0).to(device)
                with torch.no_grad():
                    vector = mobilenet(tensor).cpu().numpy().flatten().tolist()
                detected.append({
                    "label": label,
                    "vector": vector
                })
            except Exception as e:
                continue
    return detected

if __name__ == "__main__":
    with open("documents.json", "r", encoding="utf-8") as f:
        docs = json.load(f)[:500]

    for doc in tqdm(docs):
        url = doc["url"]
        image = robust_download(url)
        objects = extract_objects(image)
        doc["detected_objects"] = objects

    with open("output_vectors.json", "w") as f:
        json.dump(docs, f, indent=2)

    print("Terminé ! Résultats enrichis avec objets détectés.")
