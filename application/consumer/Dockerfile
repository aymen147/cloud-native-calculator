# Utilise Python 3.11 comme base
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie requirements.txt
COPY requirements.txt .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code de l'application
COPY consumer.py .

# Commande de démarrage
CMD ["python", "consumer.py"]
