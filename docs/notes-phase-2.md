# Notes de la phase 2 : route `/chat` et page de chat (22/11/2026)

## 1. La route `POST /chat` (8/11)

### Pourquoi deux classes, `UserMessageRequest` et `Message` ?
Afin de différencier le front et le back : UserMessageRequest qui sert pour le front, Message pour le back, qui gère la conversation avec le modèle. Il permet aussi de différencier les messages utilisateurs des réponses d'Ollama, pas de {"role": "assistant", "content": "..."} possible pour le user

### Comment les messages vides, faits seulement d'espaces ou trop longs sont-ils refusés, et avec quel code ?
Avec min_length=1 et max_length=4000. Le str_strip_whitespace=True gère les espaces

### Où est gardé l'historique, et pourquoi n'est-il enregistré qu'après la réponse d'Ollama ?
Dans la liste `history` (des objets `Message`), au niveau du module : une seule conversation partagée pour l'instant. On n'enregistre qu'après la réponse d'Ollama : sinon, en cas d'erreur, l'historique garderait un message utilisateur sans réponse, et à la question suivante le modèle recevrait deux messages utilisateur d'affilée.

## 2. L'erreur 503 et les tests avec `monkeypatch` (12/11)

### Pourquoi répondre 503 quand Ollama est arrêté, et quelle exception attrape-t-on ?
Le code d'erreur 503 indique "Service Unavailable", ce qui correspond parfaitement au fait qu'Ollama soit arrêté. On attrape alors une ConnectionError.

### Pourquoi ne pas écrire un `except:` sans type d'exception ?
Car un except sans type d'exception capture tous les types d'exceptions, dont les erreurs de code, de syntaxe etc..., ce qui rend le débogage très difficile en cas d'erreur. 

### À quoi sert `monkeypatch` sur `call_ollama`, et comment vérifier qu'un test protège vraiment le code ?
monkeypatch permet de remplacer temporairement la fonction call_ollama par un faux comportement pour tester l'API sans dépendre du vrai serveur local. On vérifie qu'il protège le code en s'assurant que le test échoue si on introduit une régression ou si on altère la logique source.

## 3. La limite de 20 messages (14/11)

### Pourquoi limiter les messages envoyés au modèle ?
Chaque modèle possède un nombre limité de tokens : il y a des tokens d'entrée et de sortie. Les tokens d'entrée sont composés du message utilisateur et de l'historique des messages. Plus l'historique est grand, plus le nombre de tokens d'entrée est important. Il faut donc respecter une limite de message - et donc de token d'entrée - afin d'éviter les erreurs liées aux dépassements de ressources

### Qu'est-ce qui n'est pas encore limité ?
Seul l'envoi au modèle est limité : l'historique stocké côté serveur grandit sans plafond

## 4. Git : le rebase (22/11)

### Qu'a fait `git rebase main` sur `feat/chat-route` ?
`feat/chat-route` était partie de `feat/backend-health` (la branche de la PR 1), avant que Théo ne fusionne les PR 1 à 3 dans main. Le rebase a rejoué les 3 commits de `feat/chat-route` par-dessus le main à jour : la PR 4 ne montre donc que ces 3 commits, et l'historique reste une ligne droite, sans commit de fusion.

### Pourquoi les hashs des commits ont-ils changé ?
Car le rebase ne déplace pas les commits : il les rejoue un par un par-dessus main, ce qui crée de nouveaux commits. Or le hash d'un commit est calculé à partir de son contenu, de son message, de ses dates et de son commit parent : le parent a changé, donc le hash aussi.

### Quand ne faut-il pas utiliser le rebase, et quelle est l'alternative ?
Comme rebase réécrit l'historique des commits, il ne faut pas l'utiliser sur les branches partagées avec d'autres, au risque de désynchroniser le travail d'équipe. L'alternative est git merge, qui crée un nouveau commit de fusion pour relier les branches sans modifier ni supprimer l'historique existant

### Pourquoi `feat/chat-page` part-elle de `feat/chat-route` et pas de `main` ?
Car nous avons besoin de la route /chat de l'API, seulement disponible sur cette branche. On crée donc une deuxième branche à partir de celle là.

## 5. React : la page de chat

### Pourquoi donner un type à `useState<Message[]>([])` ?
Car sans le type, TypeScript fait une inférence de type. Avec une liste vide, ce type est never[], c'est-à-dire un tableau qui ne peut rien contenir : le premier setMessages avec un message serait refusé.

### Qu'est-ce qu'un champ contrôlé ?
C'est un élément de formulaire (dans notre cas <input>) dont la valeur est pilotée par useState()

### Pourquoi un `<form>` avec `onSubmit` plutôt qu'un `onClick` sur le bouton, et à quoi sert `preventDefault()` ?
onSubmit réagit à la soumission complète d'un formulaire, appuyer sur Entrée permet donc d'envoyer un message. onClick réagit à l'interaction avec un élément comme un bouton.
preventDefault() sert à ne pas recharger la page - et donc tout perdre - lors de l'envoi du formulaire

### Pourquoi ne pas utiliser `messages.push(...)` ni `messages + [...]` pour ajouter un message ?
En JavaScript, + sur des tableaux les transforme en chaînes puis colle ces chaînes, alors que l'on veut ajouter des objets Message dans la liste

`messages.push(...)` ne crée pas de nouveau tableau : il modifie l'existant, sur place. Or, pour savoir s'il doit réafficher la page, React compare la référence de l'ancien état et celle du nouveau. Après un `push`, ce sont deux références vers le même tableau : React conclut que rien n'a changé et ne réaffiche rien. Avec `[...prev, x]`, on crée un nouveau tableau, donc une nouvelle référence : React voit la différence et réaffiche.

### À quoi sert la forme `setMessages((prev) => ...)` après un `await` ?
Après l'await, la variable `messages` contient encore la liste du moment où `handleSubmit` a démarré, sans le message de l'utilisateur ajouté juste avant. Avec la forme `setMessages((prev) => ...)`, React donne à la fonction la liste la plus récente (`prev`), qui contient déjà ce message : la réponse d'ALIS s'ajoute à la suite au lieu de l'effacer.

### Pourquoi l'index suffit-il comme `key` dans cette liste ?
Car on ajoute les messages à la fin de la liste et que les messages déjà affichés ne changent pas (ni supprimés, ni réordonnés).

## 6. `fetch` en POST vers `/api/chat`

### Que faut-il donner à `fetch` pour envoyer un POST ?
Il faut donner l'adresse de la route (`/api/chat`), la méthode (`"POST"`), un en-tête `Content-Type: application/json` qui annonce que le corps est du JSON, pour que FastAPI sache le lire, et enfin le corps (`body`) : le message, converti en texte JSON avec `JSON.stringify`.

### Pourquoi `JSON.stringify({ content: ... })` et pas `JSON.stringify(texte)` ?
Car notre API ne reçoit que des objets sous la forme {content: "..."}. JSON.stringify(texte) ne renverrait qu'un string comme "Bonjour", alors que l'API attend {content: "Bonjour"}

### Pourquoi tester `response.ok` ?
Car fetch n'échoue de lui-même qu'en cas de panne réseau. Sans ce test, une réponse 404, 422 ou 503 serait considérée comme une réussite.

### Que garantit `: Message` (ou `as Message`) sur la réponse, et que ne garantit-il pas ?
Pendant l'écriture du code, il permet à TypeScript de vérifier que la variable est utilisée correctement (autocomplétion de `role` et `content`, erreur sur une faute comme `contnt`). Il ne garantit pas que le serveur renvoie vraiment un Message : le type est effacé à la compilation, donc rien n'est vérifié quand le code tourne, contrairement à Pydantic.

## 7. TypeScript : l'import des types

### Pourquoi écrire `type SubmitEvent` dans l'import de `'react'` ?
Sans cet import, SubmitEvent désigne le type natif du navigateur, qui ne prend pas de <HTMLFormElement> : TypeScript répondra « Type 'SubmitEvent' is not generic ».

### Pourquoi `SubmitEvent` plutôt que `FormEvent` ?
React avait créé un type générique fourre-tout (FormEvent) pour regrouper plusieurs événements de formulaire (submit, change, input, reset, invalid). Depuis @types/react 19.2.10 (début 2026), FormEvent est déprécié, afin d'utiliser des types exacts correspondant aux événements natifs du DOM, dont notre type SubmitEvent 

## 8. Ce qui reste à faire

### Que manque-t-il à la page de chat avant d'ouvrir sa PR ?
Il manque l'état d'attente entre les messages et la gestion des erreurs.

### Quelles limites de la PR 4 restent à traiter dans les prochaines PR ?
Seul l'envoi au modèle est limité : l'historique stocké côté serveur grandit sans plafond
Pour le moment, il ne peut y avoir qu'une seule conversation, le multi-utilisateur n'est pas géré
call_ollama fait toujours un print des tokens pour le débogage
