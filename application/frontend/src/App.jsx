import Calculator from './components/Calculator'

function App() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 to-gray-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        <Calculator />
        <div className="text-center text-gray-400 text-sm font-medium">
          Modern Calculator
        </div>
      </div>
    </div>
  )
}

export default App