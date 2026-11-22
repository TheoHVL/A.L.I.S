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

  function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault() // sinon le navigateur recharge la page et tout est perdu
    const trimmedMessage = draft.trim()
    if (trimmedMessage === "") {
      return
    }
    setMessages([...messages, {role: "user", content: trimmedMessage}])
    setDraft("")
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
