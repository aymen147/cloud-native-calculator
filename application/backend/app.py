from flask import Flask, request, jsonify
import uuid
import redis
import json
import pika
import os
from flask_cors import CORS  # ← AJOUTE CETTE LIGNE


app = Flask(__name__)
CORS(app)  # ← AJOUTE CETTE LIGNE pour autoriser toutes les origines

REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Connexion à Redis
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    r.ping()
    print("✅ Connecté à Redis")
except redis.ConnectionError:
    print("❌ Erreur: Redis n'est pas accessible")
    r = None

# Connexion à RabbitMQ
def get_rabbitmq_connection():
    """Crée une connexion à RabbitMQ"""
    RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'localhost')
    RABBITMQ_PORT = int(os.getenv('RABBITMQ_PORT', 5672))
    try:
        connection = pika.BlockingConnection(
            pika.ConnectionParameters(RABBITMQ_HOST, RABBITMQ_PORT, heartbeat=600)
        )
        channel = connection.channel()
        # Déclare la file d'attente
        channel.queue_declare(queue='calculations', durable=True)
        print("✅ Connecté à RabbitMQ")
        return connection, channel
    except Exception as e:
        print(f"❌ Erreur connexion RabbitMQ: {e}")
        return None, None

@app.route('/')
def home():
    return jsonify({
        "message": "Calculator API with Redis & RabbitMQ",
        "version": "3.0",
        "redis_status": "connected" if r else "disconnected",
        "endpoints": {
            "POST /api/operation": "Submit a calculation (async)",
            "GET /api/result/<id>": "Get calculation result",
            "GET /api/operations": "List all operations"
        }
    })

@app.route('/api/operation', methods=['POST'])
def create_operation():
    """
    Reçoit une opération et l'envoie dans RabbitMQ
    (Ne calcule PLUS directement !)
    """
    if not r:
        return jsonify({"error": "Redis not available"}), 503
    
    try:
        data = request.get_json()
        
        # Validation des données
        if not data or 'operator' not in data or 'operand1' not in data or 'operand2' not in data:
            return jsonify({"error": "Missing required fields: operator, operand1, operand2"}), 400
        
        operator = data['operator']
        operand1 = float(data['operand1'])
        operand2 = float(data['operand2'])
        
        # Validation de l'opérateur
        if operator not in ['+', '-', '*', '/']:
            return jsonify({"error": "Invalid operator. Use: +, -, *, /"}), 400
        
        # Génération d'un ID unique
        operation_id = str(uuid.uuid4())
        
        # Stockage de l'opération dans Redis (statut: pending)
        operation_data = {
            "operator": operator,
            "operand1": operand1,
            "operand2": operand2,
            "status": "pending"
        }
        r.set(f"operation:{operation_id}", json.dumps(operation_data))
        
        # NOUVEAU : Envoie le message dans RabbitMQ
        connection, channel = get_rabbitmq_connection()
        if channel:
            message = {
                "id": operation_id,
                "operator": operator,
                "operand1": operand1,
                "operand2": operand2
            }
            
            channel.basic_publish(
                exchange='',
                routing_key='calculations',
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Message persistant
                )
            )
            connection.close()
            print(f"📨 Message envoyé dans RabbitMQ: {operation_id}")
        else:
            return jsonify({"error": "RabbitMQ not available"}), 503
        
        return jsonify({
            "id": operation_id,
            "message": "Operation submitted successfully",
            "status": "pending"  # ⚠️ Maintenant "pending" au lieu de "completed"
        }), 201
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/result/<operation_id>', methods=['GET'])
def get_result(operation_id):
    """
    Récupère le résultat d'une opération depuis Redis
    """
    if not r:
        return jsonify({"error": "Redis not available"}), 503
    
    try:
        # Vérifier si l'opération existe
        operation_data = r.get(f"operation:{operation_id}")
        if not operation_data:
            return jsonify({"error": "Operation not found"}), 404
        
        operation = json.loads(operation_data)
        
        # Vérifier si le résultat est disponible
        result_data = r.get(f"result:{operation_id}")
        if not result_data:
            return jsonify({
                "id": operation_id,
                "status": "pending",
                "message": "Calculation in progress"
            }), 202
        
        result = json.loads(result_data)
        
        # Vérifier si c'est une erreur
        if isinstance(result, dict) and "error" in result:
            return jsonify({
                "id": operation_id,
                "status": "error",
                "error": result["error"]
            }), 400
        
        return jsonify({
            "id": operation_id,
            "status": "completed",
            "result": result,
            "operation": operation
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/operations', methods=['GET'])
def list_operations():
    """
    Liste toutes les opérations stockées dans Redis
    """
    if not r:
        return jsonify({"error": "Redis not available"}), 503
    
    try:
        operation_keys = r.keys("operation:*")
        operations = {}
        for key in operation_keys:
            operation_id = key.replace("operation:", "")
            operation_data = r.get(key)
            if operation_data:
                operations[operation_id] = json.loads(operation_data)
        
        return jsonify({
            "total": len(operations),
            "operations": operations
        }), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health():
    """
    Endpoint de santé
    """
    redis_status = "healthy"
    try:
        if r:
            r.ping()
        else:
            redis_status = "disconnected"
    except:
        redis_status = "error"
    
    rabbitmq_status = "healthy"
    try:
        conn, ch = get_rabbitmq_connection()
        if conn:
            conn.close()
        else:
            rabbitmq_status = "disconnected"
    except:
        rabbitmq_status = "error"
    
    return jsonify({
        "api": "healthy",
        "redis": redis_status,
        "rabbitmq": rabbitmq_status
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)