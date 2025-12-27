# Utilise Python 3.11 comme base
FROM python:3.11-slim

# Définit le répertoire de travail
WORKDIR /app

# Copie requirements.txt
COPY requirements.txt .

# Installe les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copie le code de l'application
COPY app.py .

# Expose le port 5000
EXPOSE 5000

# Variable d'environnement pour Flask
ENV FLASK_APP=app.py

# Commande de démarrage
CMD ["python", "app.py"]
