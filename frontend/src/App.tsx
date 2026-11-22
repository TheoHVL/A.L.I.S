import { useState, useEffect, type SubmitEvent} from 'react'

type Message = {
  role: "user" | "assistant";
  content: string;
}

function App() {
  const [statut, setStatut] = useState('Chargement...')
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState("")

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setStatut(d.status))
      .catch(() => setStatut('serveur injoignable'))
  }, [])

  const messageItems = messages.map((message,index) => (
    <div key={index}>
        <strong>{message.role === "user" ? "Toi" : "ALIS"} : </strong>
        <span>{message.content}</span>
    </div>
  ))

  async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    const trimmedMessage = draft.trim()
    if (trimmedMessage === "") {
      return
    }

    const userMessage: Message = { role: "user", content: trimmedMessage }
    
    setMessages((prev) => [...prev, userMessage])
    setDraft("")

    try {
      const response = await fetch('/api/chat', {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content: trimmedMessage }), 
      })

      if (!response.ok) {
        throw new Error(`Erreur serveur : ${response.status}`)
      }

      const assistantMessage: Message = await response.json()
      setMessages((prev) => [...prev, assistantMessage])
      
    } catch (error) {
      console.error("Erreur lors de l'envoi :", error)
      setMessages((prev) => [
        ...prev, 
        { role: "assistant", content: "Désolé, une erreur est survenue." }
      ])
    }
  }

  return (
    <>
    <h1>ALIS</h1>
    <p>État de l'API : {statut}</p>
    <div>{messageItems}</div>


  <form onSubmit={handleSubmit}>
    <input value={draft} onChange={(e) => setDraft(e.target.value)} />
    <button type="submit">Envoyer</button>
  </form>
    </>
  )
}
export default App
