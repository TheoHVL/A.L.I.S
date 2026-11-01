# Notes de la phase 1 : backend et frontend (31/10/2026)

## 1. FastAPI, uv et le test de `/health`

### Que fait la route `/health` et pourquoi en avoir une ?
La route `/health` indique que le serveur backend est démarré et qu'il répond (`{"status": "ok"}`). Le frontend l'appelle pour savoir si le backend est joignable. Elle permet de situer rapidement l'origine d'un problème : si `/health` répond, le backend tourne et le souci est ailleurs. Elle servira aussi plus tard à la CI et au déploiement, pour savoir si l'application est vivante.

### Comment est-elle testée ?
`TestClient` appelle le code de l'application directement, dans le même processus, sans réseau et sans lancer de vrai serveur. Le test vérifie que la route renvoie le code 200 et `{"status": "ok"}`. Il est donc rapide et ne dépend d'aucun serveur démarré.

### Quel piège uv a-t-il posé (29/10) ?
`fastapi[standard]` dépend de `pyyaml`. Avec Python 3.15, que uv choisissait par défaut, `pyyaml` n'avait pas de version précompilée : il fallait la compiler sur la machine, et les outils de compilation C++ de Windows n'étaient pas installés, d'où l'échec. Avec Python 3.13, une version précompilée existe et rien n'est à compiler. `uv python pin 3.13` fixe la version de Python pour le projet (fichier `.python-version`), et uv utilise alors la bonne.

## 2. Le proxy Vite

### Quel problème le proxy résout-il ?
Une origine se compose du protocole, du domaine et du port. Le frontend (`localhost:5173`) et le backend (`127.0.0.1:8000`) sont donc deux origines différentes, même s'ils font partie de la même application. Le navigateur applique la règle de même origine (*same-origin policy*) et bloque la lecture de la réponse, sauf si le backend envoie les bons en-têtes CORS. Avec le proxy, le navigateur appelle `/api/health` sur le port du frontend (même origine), et c'est Vite qui relaie la requête vers le backend, de serveur à serveur, sans règle de navigateur. On évite ainsi d'avoir à configurer CORS en développement.

### Que fait `rewrite` ?
`rewrite` réécrit le chemin des requêtes interceptées. Toutes les routes qui commencent par `/api` sont relayées vers le backend, et le préfixe est retiré, car le backend n'a pas de préfixe `/api` : `/api/health` devient `/health`.

### Y a-t-il une limite ?
Le proxy fait partie du serveur de développement de Vite, il ne fonctionne donc qu'avec `npm run dev`. `npm run build` ne produit que des fichiers statiques, sans Vite derrière. En production, il faudra un autre mécanisme : un reverse proxy (par exemple Nginx) devant les deux services, ou une configuration CORS sur le backend.

## 3. React : `useState`, `useEffect` et `fetch`

### À quoi sert `useState` dans `App.tsx` ?
`useState` crée une variable d'état : dans `App.tsx`, `statut` vaut `'Chargement...'` au départ, et `setStatut` sert à la modifier. Une variable ordinaire changerait en mémoire sans que l'écran soit mis à jour. Quand on appelle `setStatut(d.status)`, React réaffiche le composant avec la nouvelle valeur, et la page passe de « Chargement... » à « ok ».

### Pourquoi `fetch` est-il dans un `useEffect` avec `[]`, et que se passe-t-il sans ce `[]` ?
`useEffect` sert à lancer une action après l'affichage du composant, ici l'appel à `/api/health`. Le tableau vide `[]` signifie « une seule fois, au premier affichage ». Sans lui, l'effet s'exécuterait après chaque affichage. Dans `App.tsx`, cela donnerait une boucle sans fin : l'effet appelle `setStatut`, ce qui réaffiche le composant, ce qui relance l'effet, donc un nouveau `fetch`, et ainsi de suite. En développement, `StrictMode` (dans `main.tsx`) exécute l'effet deux fois au premier affichage : c'est normal, on voit alors deux appels `/health` dans les logs du backend.

### À quoi sert `.catch` ? Que voit l'utilisateur quand le backend est arrêté ?
`.catch` s'exécute quand la chaîne du `fetch` échoue pendant que la page tourne, par exemple quand la requête n'aboutit pas ou que `r.json()` n'arrive pas à lire la réponse. Il n'a aucun rapport avec la compilation. Quand le backend est arrêté, l'utilisateur voit « État de l'API : serveur injoignable ». À noter : `fetch` ne considère pas une réponse 404 ou 500 comme une erreur. Ici, le `.catch` s'active quand même, parce que Vite renvoie une erreur sans JSON et que `r.json()` échoue, mais ce n'est pas une garantie générale.

## 4. Le conflit de dépendances TypeScript 7 et `typescript-eslint`

### Quel était le message d'erreur et que disait-il ?
Le code d'erreur était `ERESOLVE` (« unable to resolve dependency tree »). Le message d'erreur venait d'un conflit de version de TypeScript entre 2 paquets. Le modèle de projet a indiqué qu'il travaillait par défaut avec la dernière version de TypeScript (7.0.2), sauf que `typescript-eslint` déclare qu'il fonctionne avec TypeScript `>=4.8.4 <6.1.0`, c'est donc une *peer dependency* : une dépendance que `typescript-eslint` attend d'être installée par le projet, avec une version précise.

### Pourquoi ne pas utiliser `--legacy-peer-deps` ?
`--legacy-peer-deps` force l'installation d'une combinaison instable qui pourrait faire crasher `npm run lint` sans qu'on en connaisse la raison.

### Comment le conflit a-t-il été réglé ?
Dans le `package.json`, qui gère les dépendances, on a remplacé `"typescript": "~7.0.2"` par la bonne version de TypeScript à utiliser, `"~6.0.3"`. `npm run build` lance `tsc -b`, qui vérifie que tous les types correspondent avec TypeScript 6. `npm run lint` ne renvoie rien, ce qui indique que tout passe. À noter : quand `typescript-eslint` marchera avec TypeScript 7, il suffira de modifier 1 ligne pour le mettre à jour.

## 5. Git : branches séparées et PR

### Pourquoi une branche et une PR séparées pour le backend et le frontend ?
La séparation isole les 2 travaux : on peut modifier l'un, ou annuler ses modifications, sans toucher à l'autre. Pour la relecture, elle permet aussi de relire et valider le frontend sans attendre le backend. À noter : lorsque la PR n°1 sera fusionnée dans `main`, la branche du frontend aura alors le backend, ce qui enlèvera la contrainte de test décrite plus bas.

### Quel problème cette séparation a-t-elle posé pour tester ?
L'erreur « Path does not exist app/main.py » est survenue au moment de tester le front, car la branche du frontend, créée depuis `main`, n'avait pas le code du backend, et donc pas le `main.py` requis.

### Comment le problème a-t-il été résolu ?
On a changé de branche pour aller sur celle du backend. Le dossier `frontend/` n'étant pas encore suivi par Git (*untracked*), il est conservé tel quel lors du changement de branche. On est ensuite revenu sur `feat/frontend-health` pour committer.
