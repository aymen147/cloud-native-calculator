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
