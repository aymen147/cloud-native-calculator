from flask import Flask, request, jsonify
import uuid

app = Flask(__name__)

# Stockage temporaire en mémoire (sera remplacé par Redis)
operations = {}
results = {}

@app.route('/')
def home():
    return jsonify({
        "message": "Calculator API",
        "version": "1.0",
        "endpoints": {
            "POST /api/operation": "Submit a calculation",
            "GET /api/result/<id>": "Get calculation result"
        }
    })

@app.route('/api/operation', methods=['POST'])
def create_operation():
    """
    Reçoit une opération à calculer
    Exemple: {"operator": "+", "operand1": 5, "operand2": 3}
    """
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
        
        # Stockage de l'opération
        operations[operation_id] = {
            "operator": operator,
            "operand1": operand1,
            "operand2": operand2,
            "status": "pending"
        }
        
        # Pour l'instant, on calcule directement (plus tard ce sera le Consumer)
        if operator == '+':
            result = operand1 + operand2
        elif operator == '-':
            result = operand1 - operand2
        elif operator == '*':
            result = operand1 * operand2
        elif operator == '/':
            if operand2 == 0:
                results[operation_id] = {"error": "Division by zero"}
            else:
                result = operand1 / operand2
        
        # Stockage du résultat
        if operation_id not in results:
            results[operation_id] = result
        
        operations[operation_id]["status"] = "completed"
        
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
    Récupère le résultat d'une opération
    """
    # Vérifier si l'opération existe
    if operation_id not in operations:
        return jsonify({"error": "Operation not found"}), 404
    
    # Vérifier si le résultat est disponible
    if operation_id not in results:
        return jsonify({
            "id": operation_id,
            "status": "pending",
            "message": "Calculation in progress"
        }), 202
    
    result = results[operation_id]
    
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
        "result": result
    }), 200

@app.route('/api/operations', methods=['GET'])
def list_operations():
    """
    Liste toutes les opérations (utile pour débugger)
    """
    return jsonify({
        "total": len(operations),
        "operations": operations
    }), 200

if __name__ == '__main__':
    # Port 5000 par défaut pour Flask
    app.run(host='0.0.0.0', port=5000, debug=True)