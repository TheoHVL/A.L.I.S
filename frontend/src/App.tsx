import { useState, useEffect } from 'react'

function App() {
  const [statut, setStatut] = useState('Chargement...')
  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setStatut(d.status))
      .catch(() => setStatut('serveur injoignable'))
  }, [])
  return (
    <>
    <h1>ALIS</h1>
    <p>État de l'API : {statut}</p>
    </>
  )
}

export default App
