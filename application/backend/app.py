from flask import Flask, request, jsonify
import uuid
import redis
import json

app = Flask(__name__)

# Connexion à Redis
try:
    r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    r.ping()  # Test de connexion
    print("✅ Connecté à Redis")
except redis.ConnectionError:
    print("❌ Erreur: Redis n'est pas accessible")
    r = None

@app.route('/')
def home():
    return jsonify({
        "message": "Calculator API with Redis",
        "version": "2.0",
        "redis_status": "connected" if r else "disconnected",
        "endpoints": {
            "POST /api/operation": "Submit a calculation",
            "GET /api/result/<id>": "Get calculation result",
            "GET /api/operations": "List all operations"
        }
    })

@app.route('/api/operation', methods=['POST'])
def create_operation():
    """
    Reçoit une opération à calculer
    Exemple: {"operator": "+", "operand1": 5, "operand2": 3}
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
        
        # Stockage de l'opération dans Redis
        operation_data = {
            "operator": operator,
            "operand1": operand1,
            "operand2": operand2,
            "status": "pending"
        }
        r.set(f"operation:{operation_id}", json.dumps(operation_data))
        
        # Pour l'instant, on calcule directement (plus tard ce sera le Consumer)
        if operator == '+':
            result = operand1 + operand2
        elif operator == '-':
            result = operand1 - operand2
        elif operator == '*':
            result = operand1 * operand2
        elif operator == '/':
            if operand2 == 0:
                result = {"error": "Division by zero"}
            else:
                result = operand1 / operand2
        
        # Stockage du résultat dans Redis
        r.set(f"result:{operation_id}", json.dumps(result))
        
        # Mise à jour du statut
        operation_data["status"] = "completed"
        r.set(f"operation:{operation_id}", json.dumps(operation_data))
        
        return jsonify({
            "id": operation_id,
            "message": "Operation submitted successfully",
            "status": "completed"
        }), 201
        
    except Exception as e:
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
        # Récupérer toutes les clés d'opérations
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
    Endpoint de santé pour vérifier le statut de l'API et Redis
    """
    redis_status = "healthy"
    try:
        if r:
            r.ping()
        else:
            redis_status = "disconnected"
    except:
        redis_status = "error"
    
    return jsonify({
        "api": "healthy",
        "redis": redis_status
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)