import { useState } from 'react'
import { submitOperation, getResult } from '../services/api'

export default function Calculator() {
  const [display, setDisplay] = useState('0')
  const [currentOperator, setCurrentOperator] = useState(null)
  const [operand1, setOperand1] = useState(null)
  const [waitingForOperand, setWaitingForOperand] = useState(false)

  const handleNumber = (num) => {
    if (waitingForOperand) {
      setDisplay(String(num))
      setWaitingForOperand(false)
    } else {
      setDisplay(display === '0' ? String(num) : display + num)
    }
  }

  const handleOperator = (operator) => {
    const num = parseFloat(display)
    
    if (operand1 === null) {
      setOperand1(num)
    } else if (currentOperator && !waitingForOperand) {
      performCalculation()
      return
    }
    
    setWaitingForOperand(true)
    setCurrentOperator(operator)
  }

  const performCalculation = async () => {
    if (currentOperator === null || waitingForOperand) return

    const operand2 = parseFloat(display)
    if (isNaN(operand1) || isNaN(operand2)) return

    try {
      const { id } = await submitOperation(currentOperator, operand1, operand2)
      setDisplay('...')
      
      const result = await pollResult(id)
      setDisplay(String(result))
      setOperand1(result)
      setWaitingForOperand(true)
      setCurrentOperator(null)
    } catch (error) {
      setDisplay('Error')
      setTimeout(() => {
        setDisplay('0')
        setOperand1(null)
        setCurrentOperator(null)
        setWaitingForOperand(false)
      }, 1500)
    }
  }

  const pollResult = async (id, attempts = 0) => {
    const maxAttempts = 20
    const data = await getResult(id)

    if (data.status === 'completed') {
      return data.result
    } else if (data.status === 'pending' && attempts < maxAttempts) {
      await new Promise(resolve => setTimeout(resolve, 500))
      return pollResult(id, attempts + 1)
    } else {
      throw new Error(data.error || 'Timeout')
    }
  }

  const handleClear = () => {
    setDisplay('0')
    setOperand1(null)
    setCurrentOperator(null)
    setWaitingForOperand(false)
  }

  const handleToggleSign = () => {
    const num = parseFloat(display)
    if (!isNaN(num)) {
      setDisplay(String(-num))
    }
  }

  const handlePercent = () => {
    const num = parseFloat(display)
    if (!isNaN(num)) {
      setDisplay(String(num / 100))
    }
  }

  const handleDecimal = () => {
    if (!display.includes('.')) {
      setDisplay(display + '.')
    }
  }

  const buttons = [
    { label: 'AC', onClick: handleClear, color: 'gray' },
    { label: '±', onClick: handleToggleSign, color: 'gray' },
    { label: '%', onClick: handlePercent, color: 'gray' },
    { label: '÷', onClick: () => handleOperator('/'), color: 'orange', isOperator: true },
    
    { label: '7', onClick: () => handleNumber(7), color: 'dark' },
    { label: '8', onClick: () => handleNumber(8), color: 'dark' },
    { label: '9', onClick: () => handleNumber(9), color: 'dark' },
    { label: '×', onClick: () => handleOperator('*'), color: 'orange', isOperator: true },
    
    { label: '4', onClick: () => handleNumber(4), color: 'dark' },
    { label: '5', onClick: () => handleNumber(5), color: 'dark' },
    { label: '6', onClick: () => handleNumber(6), color: 'dark' },
    { label: '-', onClick: () => handleOperator('-'), color: 'orange', isOperator: true },
    
    { label: '1', onClick: () => handleNumber(1), color: 'dark' },
    { label: '2', onClick: () => handleNumber(2), color: 'dark' },
    { label: '3', onClick: () => handleNumber(3), color: 'dark' },
    { label: '+', onClick: () => handleOperator('+'), color: 'orange', isOperator: true },
    
    { label: '0', onClick: () => handleNumber(0), color: 'dark', wide: true },
    { label: '.', onClick: handleDecimal, color: 'dark' },
    { label: '=', onClick: performCalculation, color: 'orange' },
  ]

  const getButtonClass = (color, wide = false, isActive = false) => {
    let baseClass = 'h-20 rounded-2xl font-semibold text-3xl transition-all duration-150 active:scale-95 select-none cursor-pointer shadow-md'

    if (wide) {
      baseClass += ' col-span-2'
    }

    if (color === 'orange') {
      return `${baseClass} ${isActive ? 'bg-white text-orange-500' : 'bg-orange-500 text-white'} hover:bg-orange-400`
    } else if (color === 'gray') {
      return `${baseClass} bg-gray-600 text-white hover:bg-gray-500`
    } else {
      return `${baseClass} bg-gray-700 text-white hover:bg-gray-600`
    }
  }

  return (
    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-3xl p-6 shadow-2xl">
      {/* Display */}
      <div className="mb-6 px-4 py-8 bg-gray-900 rounded-2xl">
        <div className="text-white text-7xl font-light text-right tracking-tight">
          {display.length > 9 ? display.slice(0, 9) : display}
        </div>
      </div>

      {/* Buttons Grid */}
      <div className="grid grid-cols-4 gap-3">
        {buttons.map((btn, idx) => {
          const isActiveOperator = btn.isOperator && btn.label === getOperatorSymbol(currentOperator) && waitingForOperand
          
          return (
            <button
              key={idx}
              onClick={btn.onClick}
              className={getButtonClass(btn.color, btn.wide, isActiveOperator)}
            >
              {btn.label}
            </button>
          )
        })}
      </div>
    </div>
  )
}

function getOperatorSymbol(operator) {
  const symbols = {
    '+': '+',
    '-': '-',
    '*': '×',
    '/': '÷'
  }
  return symbols[operator] || operator
}