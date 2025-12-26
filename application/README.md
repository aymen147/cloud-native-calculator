## Exemple of Testing Post Backend in Fastapi 
curl.exe -X POST http://localhost:5000/api/operation -H "Content-Type: application/json" -d '{\"operator\": \"+\", \"operand1\": 10, \"operand2\": 5}'

## response : 
{
  "id": "id",
  "message": "Operation submitted successfully",
  "status": "completed"
}

## Get Result of response  : 
 curl.exe http://localhost:5000/api/result/id

## response :
{
  "id": "id",
  "result": 15.0,
  "status": "completed"
}

## Open Redis db 
docker run -p 6379:6379 --name myredis --rm redis

## Verifier Redis db Setter
docker exec -it myredis redis-cli
127.0.0.1:6379> KEYS *
1) "docker:test"
2) "result:id"
3) "operation:id"

## Lancer RabbitMQ avec Docker
docker run -it --rm --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3.12-management

**Explication :**
- `-p 5672:5672` : Port pour les messages (communication)
- `-p 15672:15672` : Port pour l'interface web (monitoring)
- `rabbitmq:3.12-management` : Version avec interface de gestion

### 📖 Qu'est-ce que le Consumer ?
Le Consumer est un programme séparé qui :

Écoute RabbitMQ en permanence
Récupère les messages de calcul
Effectue les calculs
Stocke les résultats dans Redis






