# 1. Uporabimo lažjo osnovo
FROM python:3.9-slim

# 2. Namestimo sistemske odvisnosti (samo tisto, kar je nujno)
# Združimo v en RUN in na koncu počistimo cache, da je slika manjša
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 3. NAJPREJ skopiramo samo datoteko z odvisnostmi
COPY requirements.txt .

# 4. Inštaliraš knjižnice (Docker bo to shranil v cache!)
RUN pip install --no-cache-dir -r requirements.txt

# 5. ŠELE NA KONCU skopiraš ostalo kodo
COPY . .

# Če uporabljaš uvicorn (priporočeno za FastAPI):
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

# ALI če zagon delaš direktno s pythonom (manj verjetno):
# CMD ["python", "main.py"]