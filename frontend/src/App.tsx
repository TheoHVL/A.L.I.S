import { useState, useEffect, useRef, type SubmitEvent } from 'react'
import { streamChat } from './api/chatStream'

type Message = {
  role: "user" | "assistant";
  content: string;
}

function App() {
  const [statut, setStatut] = useState('Chargement...')
  const [messages, setMessages] = useState<Message[]>([])
  const [draft, setDraft] = useState("")
  const [isStreaming, setIsStreaming] = useState(false)
  const controllerRef = useRef<AbortController | null>(null)

  useEffect(() => {
    fetch('/api/health')
      .then((r) => r.json())
      .then((d) => setStatut(d.status))
      .catch(() => setStatut('serveur injoignable'))
  }, [])

  const messageItems = messages.map((message, index) => (
    <div key={index}>
      <strong>{message.role === "user" ? "Toi" : "ALIS"} : </strong>
      <span>{message.content}</span>
    </div>
  ))

  function updateLastMessage(update: (content: string) => string) {
    setMessages((prev) => {
      const last = prev[prev.length - 1]
      return [...prev.slice(0, -1), { ...last, content: update(last.content) }]
    })
  }

  async function handleSubmit(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault()
    const trimmedMessage = draft.trim()
    if (trimmedMessage === "" || isStreaming) {
      return
    }

    setMessages((prev) => [
      ...prev,
      { role: "user", content: trimmedMessage },
      { role: "assistant", content: "" },
    ])
    setDraft("")

    const controller = new AbortController()
    controllerRef.current = controller
    setIsStreaming(true)

    try {
      await streamChat(trimmedMessage, controller.signal, (event) => {
        if (event.type === "token") {
          updateLastMessage((content) => content + event.texte)
        } else if (event.type === "erreur") {
          updateLastMessage(() => `Erreur : ${event.message}`)
        }
      })
    } catch (error) {
      if (error instanceof DOMException && error.name === "AbortError") {
        updateLastMessage((content) => content + " [arrêté]")
      } else {
        console.error("Erreur lors de l'envoi :", error)
        updateLastMessage(() => "Désolé, une erreur est survenue.")
      }
    } finally {
      controllerRef.current = null
      setIsStreaming(false)
    }
  }

  function handleStop() {
    controllerRef.current?.abort()
  }

  return (
    <>
      <h1>ALIS</h1>
      <p>État de l'API : {statut}</p>
      <div>{messageItems}</div>

      <form onSubmit={handleSubmit}>
        <input value={draft} onChange={(e) => setDraft(e.target.value)} />
        {isStreaming ? (
          <button type="button" onClick={handleStop}>Stop</button>
        ) : (
          <button type="submit">Envoyer</button>
        )}
      </form>
    </>
  )
}
export default App