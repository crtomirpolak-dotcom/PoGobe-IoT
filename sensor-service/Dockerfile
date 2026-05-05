# Uporabimo uradno Python sliko
FROM python:3.10-slim

# Nastavimo delovni imenik v kontejnerju
WORKDIR /app

# Kopiramo datoteko z zahtevanimi knjižnicami
COPY requirements.txt .

# Namestimo knjižnice
RUN pip install --no-cache-dir -r requirements.txt

# Kopiramo preostalo kodo v kontejner
COPY . .

# Odpremo port 8000 (notranji port)
EXPOSE 8000

# Ukaz za zagon aplikacije
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]