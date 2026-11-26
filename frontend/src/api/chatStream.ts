// Contrat des événements : voir docs/evenements-sse.md
export type StreamEvent =
  | { type: "token"; texte: string }
  | { type: "erreur"; message: string }
  | { type: "fin" }

export async function streamChat(
  content: string,
  signal: AbortSignal,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  })

  if (!response.ok || !response.body) {
    throw new Error(`Erreur serveur : ${response.status}`)
  }

  const reader = response.body.pipeThrough(new TextDecoderStream()).getReader()
  let buffer = ""

  while (true) {
    const { value, done } = await reader.read()
    if (done) break

    buffer += value
    const blocks = buffer.split("\n\n")
    buffer = blocks.pop() ?? "" // le dernier bloc peut être incomplet

    for (const block of blocks) {
      if (!block.startsWith("data: ")) continue
      onEvent(JSON.parse(block.slice("data: ".length)) as StreamEvent)
    }
  }
}