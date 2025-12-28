const API_URL = ''

export async function submitOperation(operator, operand1, operand2) {
  const response = await fetch(`${API_URL}/api/operation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ operator, operand1, operand2 }),
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Erreur réseau')
  }
  
  return response.json()
}

export async function getResult(id) {
  const response = await fetch(`${API_URL}/api/result/${id}`)
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error || 'Erreur réseau')
  }
  
  return response.json()
}