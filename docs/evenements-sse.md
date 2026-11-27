# Événements du streaming (`POST /chat/stream`)

La route reçoit `{"content": "..."}` (même validation que `/chat`) et répond en
`text/event-stream`. Chaque événement est une ligne `data: <json>` suivie d'une ligne vide.
Le champ `type` indique la sorte d'événement.

| type     | Champs    | Quand                                                    |
|----------|-----------|----------------------------------------------------------|
| `token`  | `texte`   | un morceau de la réponse ; le front le colle à la suite |
| `erreur` | `message` | un problème pendant la génération ; le flux s'arrête     |
| `fin`    | —         | la réponse est complète et enregistrée dans l'historique |

Exemple :

```
data: {"type":"token","texte":"Bon"}

data: {"type":"token","texte":"jour"}

data: {"type":"fin"}
```

## Règles
- Le code HTTP est toujours 200 dès que le flux a commencé : une erreur arrive comme événement `erreur`.
- Un message vide ou trop long est refusé avant le flux (422).
- L'échange n'est ajouté à l'historique qu'après `fin`. Après une `erreur` ou un Stop, l'historique ne change pas.
- Stop : le front coupe la connexion (`AbortController`) ; le backend arrête de lire Ollama, qui arrête de générer.
- Phase 4 : un type `etape` s'ajoutera pour les appels d'outils de l'agent.

Les modèles Pydantic `TokenEvent`, `ErreurEvent` et `FinEvent` (`backend/app/main.py`)
et le type `StreamEvent` (`frontend/src/api/chatStream.ts`) doivent rester identiques à ce tableau.