import pika
import redis
import json
import time
import sys
import os

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))

# Connexion à Redis
print("🔄 Connexion à Redis...")
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    print("✅ Connecté à Redis")
except redis.ConnectionError as e:
    print(f"❌ Erreur Redis: {e}")
    sys.exit(1)

# Connexion à RabbitMQ
print("🔄 Connexion à RabbitMQ...")
max_retries = 5
retry_count = 0

while retry_count < max_retries:
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, heartbeat=600)
        )
        channel = connection.channel()
        channel.queue_declare(queue='calculations', durable=True)
        print("✅ Connecté à RabbitMQ")
        break
    except Exception as e:
        retry_count += 1
        print(f"⏳ Tentative {retry_count}/{max_retries} - Erreur: {e}")
        if retry_count < max_retries:
            time.sleep(2)
        else:
            print("❌ Impossible de se connecter à RabbitMQ")
            sys.exit(1)

def callback(ch, method, properties, body):
    """
    Fonction appelée automatiquement pour chaque message reçu
    """
    try:
        # Décode le message
        message = json.loads(body)
        operation_id = message['id']
        operator = message['operator']
        operand1 = message['operand1']
        operand2 = message['operand2']
        
        print(f"\n{'='*60}")
        print(f"📨 Message reçu: {operation_id}")
        print(f"🧮 Calcul: {operand1} {operator} {operand2}")
        
        # CALCUL
        if operator == '+':
            result = operand1 + operand2
        elif operator == '-':
            result = operand1 - operand2
        elif operator == '*':
            result = operand1 * operand2
        elif operator == '/':
            if operand2 == 0:
                result = {"error": "Division by zero"}
                print(f"❌ Erreur: Division par zéro")
            else:
                result = operand1 / operand2
        else:
            result = {"error": "Invalid operator"}
            print(f"❌ Opérateur invalide")
        
        # Stockage du résultat dans Redis
        r.set(f"result:{operation_id}", json.dumps(result))
        print(f"💾 Résultat stocké dans Redis: {result}")
        
        # Mise à jour du statut de l'opération
        operation_data = r.get(f"operation:{operation_id}")
        if operation_data:
            operation = json.loads(operation_data)
            operation["status"] = "completed"
            r.set(f"operation:{operation_id}", json.dumps(operation))
            print(f"✅ Statut mis à jour: completed")
        
        # Acquittement du message (retire de la file)
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print(f"✅ Message traité avec succès")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"❌ Erreur lors du traitement: {e}")
        # En cas d'erreur, on acquitte quand même pour éviter une boucle infinie
        ch.basic_ack(delivery_tag=method.delivery_tag)

# Configuration du consumer
channel.basic_qos(prefetch_count=1)  # Traite un message à la fois
channel.basic_consume(queue='calculations', on_message_callback=callback)

print("\n" + "="*60)
print("🔄 CONSUMER DÉMARRÉ - En attente de messages...")
print("="*60)
print("Appuyez sur Ctrl+C pour arrêter\n")

try:
    channel.start_consuming()
except KeyboardInterrupt:
    print("\n🛑 Arrêt du consumer...")
    channel.stop_consuming()
    connection.close()
    print("✅ Consumer arrêté proprement")