# ✈️ Voyager AI — Guide complet d'installation et d'utilisation

> Agent IA de voyage · LangChain 1.x + LangGraph + Streamlit  
> Avec évaluation RAG/Agentique intégrée (4 niveaux de métriques)

---

## 📁 Structure du projet

```
voyager_ai/
├── app.py              ← Interface Streamlit (chat + dashboard métriques)
├── agent.py            ← Agent LangGraph (create_react_agent)
├── tools.py            ← 8 outils LangChain (vols, hôtels, activités…)
├── metrics.py          ← Couche d'évaluation (Retrieval, Génération, Agentique, LLM Juge)
├── utils.py            ← Fonctions utilitaires (session state, export)
├── requirements.txt    ← Dépendances Python
└── GUIDE.md            ← Ce document
```

---

## 🔑 Étape 1 — Obtenir les clés API

### Clé OpenAI (obligatoire)

1. Allez sur **https://platform.openai.com/api-keys**
2. Connectez-vous ou créez un compte
3. Cliquez **"Create new secret key"**
4. Nommez-la (ex : `voyager-ai`) et copiez-la **immédiatement** — elle n'est visible qu'une seule fois
5. Vérifiez que vous avez du crédit : **https://platform.openai.com/usage**

> Le projet utilise `gpt-4o` par défaut (~$0.005 par requête) et `gpt-4o-mini` pour le LLM Juge (~$0.0002).

### Clé SerpAPI (optionnelle — données de vols/hôtels en temps réel)

1. Allez sur **https://serpapi.com**
2. Créez un compte gratuit (100 recherches/mois offertes)
3. Copiez votre clé depuis le dashboard : **"Your Private API Key"**

> Sans SerpAPI, le projet fonctionne avec des données simulées réalistes.

---

## 💻 Étape 2 — Préparer l'environnement Python

### Ouvrir un terminal dans le dossier du projet

```cmd
cd C:\chemin\vers\voyager_ai
```

### Créer un environnement virtuel

```cmd
python -m venv venv
```

### Activer l'environnement virtuel

**Windows (Invite de commandes) :**
```cmd
venv\Scripts\activate
```

**Windows (PowerShell) — si erreur de politique d'exécution :**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\activate
```

**Mac / Linux :**
```bash
source venv/bin/activate
```

✅ Une fois activé, vous verrez `(venv)` devant votre prompt :
```
(venv) C:\...\voyager_ai>
```

---

## 📦 Étape 3 — Installer les dépendances

```cmd
pip install -r requirements.txt
```

Cette commande installe :

| Package | Rôle |
|---------|------|
| `streamlit` | Interface web |
| `langchain` | Framework agent |
| `langgraph` | Moteur d'agent (remplace AgentExecutor) |
| `langchain-openai` | Connecteur GPT-4o |
| `langchain-community` | Outils communautaires |
| `openai` | SDK OpenAI |
| `pydantic` | Validation des données |
| `python-dotenv` | Gestion des variables d'environnement |
| `google-search-results` | SerpAPI (optionnel) |

### Vérifier l'installation

```cmd
pip show langchain langgraph langchain-openai
```

Vous devez voir des versions **≥ 1.0** pour langchain, **≥ 0.3** pour langgraph et langchain-openai.

---

## 🔐 Étape 4 — Configurer les clés API

Vous avez deux options :

### Option A — Via l'interface Streamlit (le plus simple)

Lancez l'app et collez vos clés directement dans la **barre latérale gauche** :
- Champ **"OpenAI API Key"** : coller votre clé `sk-proj-...`
- Champ **"SerpAPI Key"** : coller votre clé SerpAPI (ou laisser vide)

### Option B — Via un fichier `.env` (recommandé)

Créez un fichier `.env` à la racine du projet :

```
voyager_ai/
└── .env   ← créer ce fichier
```

Contenu du `.env` :

```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxx
SERPAPI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Puis modifiez les premières lignes de `app.py` pour charger automatiquement ces clés :

```python
# Ajouter après les imports existants dans app.py
from dotenv import load_dotenv
import os

load_dotenv()
OPENAI_KEY_DEFAULT = os.getenv("OPENAI_API_KEY", "")
SERPAPI_KEY_DEFAULT = os.getenv("SERPAPI_API_KEY", "")
```

Et dans la sidebar, modifiez les champs :

```python
openai_key = st.text_input("OpenAI API Key", value=OPENAI_KEY_DEFAULT, type="password")
serpapi_key = st.text_input("SerpAPI Key (optional)", value=SERPAPI_KEY_DEFAULT, type="password")
```

> ⚠️ **Sécurité** : ajoutez `.env` à votre `.gitignore` pour ne jamais publier vos clés :
> ```cmd
> echo .env >> .gitignore
> ```

---

## 🚀 Étape 5 — Lancer l'application

```cmd
streamlit run app.py
```

L'application s'ouvre automatiquement dans votre navigateur à l'adresse :
```
http://localhost:8501
```

Si elle ne s'ouvre pas automatiquement, copiez cette URL dans votre navigateur.

---

## 🗺️ Étape 6 — Utiliser l'agent

### Configuration initiale (sidebar gauche)

1. **Budget Range** : sélectionnez votre budget (Economy / Mid-range / Luxury / Ultra-luxury)
2. **Travel Style** : choisissez un ou plusieurs styles (Adventure, Culture, Beach…)
3. **Travelling As** : Solo, Couple, Famille, Groupe, Business
4. **Trip Duration** : nombre de jours (glissière 3–30)
5. **OpenAI API Key** : collez votre clé `sk-proj-...`
6. **SerpAPI Key** : optionnel, pour des données de vols/hôtels en temps réel

### Exemples de conversations

**Planification complète :**
```
Je veux passer 7 jours au Japon en avril. Budget 3 000€. 
J'adore la gastronomie et les temples. Voyage en couple.
```

**Questions spécifiques :**
```
Quel temps fait-il à Kyoto en avril ?
Combien vaut 500€ en yens japonais ?
Ai-je besoin d'un visa pour le Japon en tant que Français ?
```

**Réservation :**
```
Réserve le deuxième hôtel pour Jean Dupont, jean@email.com
```

### Boutons de démarrage rapide

La sidebar propose 4 destinations prêtes à l'emploi :
- 🗼 Plan a week in Paris
- 🏝️ Bali honeymoon, 10 days
- 🗽 NYC family trip, 5 days
- 🏔️ Swiss Alps adventure

---

## 📊 Étape 7 — Lire le tableau de bord de métriques

Après chaque réponse de l'agent, un panneau **"📊 Tableau de bord d'évaluation"** apparaît en bas de page. Cliquez dessus pour l'ouvrir.

### KPIs de session (ligne du haut)

| Indicateur | Description |
|-----------|-------------|
| Tours évalués | Nombre de questions posées |
| Taux grounding | % de réponses basées sur des outils (non hallucinées) |
| Pipeline complet | % de tours avec recherche + analyse + réponse |
| Risque hallucination | % de réponses sans source |
| Score LLM Juge | Note moyenne sur 5 donnée par le juge IA |

### Onglet 🔎 Retrieval

Évalue la qualité des données récupérées par les outils :

| Métrique | Interprétation |
|---------|----------------|
| Docs récupérés | Nombre total de résultats (vols, hôtels, activités) |
| Docs retenus | Après filtrage qualité (rating ≥ 4.0) |
| Score max | Meilleur score de pertinence |
| Score moyen | Qualité moyenne des résultats |
| Compression ratio | Ratio retenus/récupérés (proche de 1 = bon filtrage) |

**Alertes :**
- ⚠️ Retrieval vide : aucun outil appelé ou aucun résultat
- ⚠️ Sur-retrieval : trop de résultats, filtrage insuffisant
- ⚠️ Sous-retrieval : trop peu de résultats, requête trop restrictive

### Onglet ✍️ Génération

Évalue la qualité de la réponse produite :

| Métrique | Interprétation |
|---------|----------------|
| Réponse présente | ✅ La réponse n'est pas vide |
| Grounded | ✅ La réponse s'appuie sur des outils de recherche |
| Taille réponse | En caractères (< 50 = trop courte, > 3000 = risque d'invention) |
| Compression | Rapport taille réponse / taille contexte |

**Alertes :**
- 🚨 Hallucination potentielle : réponse non basée sur des sources
- ⚠️ Réponse trop courte ou trop longue

### Onglet 🤖 Pipeline Agentique

Évalue le comportement du pipeline multi-outils :

| Métrique | Interprétation |
|---------|----------------|
| Étapes totales | Nombre d'appels d'outils |
| Agents utilisés | Nombre d'outils distincts utilisés |
| Étapes/agent | Charge moyenne par outil |
| Pipeline complet | ✅ Recherche + Analyse + Réponse présents |
| Latence | Temps de réponse total en millisecondes |
| Séquence d'exécution | Ordre des outils appelés |

### Onglet ⚖️ LLM Juge

Évaluation qualitative par un second LLM (gpt-4o-mini) :

| Critère | Poids | Description |
|---------|-------|-------------|
| Pertinence | 35% | La réponse répond-elle à la question ? |
| Fidélité | 30% | Est-elle fidèle aux informations disponibles ? |
| Complétude | 20% | Tous les aspects sont-ils couverts ? |
| Clarté | 15% | La réponse est-elle bien structurée ? |

**Verdicts :**
- 🟢 EXCELLENT : score ≥ 4.5/5
- 🔵 BON : score ≥ 3.5/5
- 🟡 ACCEPTABLE : score ≥ 2.5/5
- 🔴 INSUFFISANT : score < 2.5/5

---

## 💾 Étape 8 — Exporter les données

### Exporter l'itinéraire (Markdown)

Dans la sidebar, cliquez **"📋 Export"** puis **"⬇️ Download"** pour télécharger la conversation en fichier `.md`.

### Exporter les rapports d'évaluation (JSON)

Dans le tableau de bord, cliquez **"⬇️ Exporter tous les rapports (JSON)"** pour télécharger l'ensemble des métriques de session au format JSON.

Format du fichier exporté :
```json
[
  {
    "turn_id": "a1b2c3d4",
    "question": "Plan a week in Japan...",
    "created_at": "2025-05-12T10:30:00",
    "retrieval": { "raw_count": 11, "selected_count": 9, ... },
    "generation": { "grounded": true, "answer_length": 1842, ... },
    "agentic": { "pipeline_complete": true, "latency_ms": 4230, ... },
    "judge": { "score_global": 4.35, "verdict": "BON", ... }
  }
]
```

---

## 🛠️ Résolution des problèmes courants

### ImportError: cannot import name 'AgentExecutor'

**Cause** : vous avez LangChain 1.x qui a supprimé `AgentExecutor`.  
**Solution** : le fichier `agent.py` fourni utilise déjà `create_react_agent` de LangGraph. Vérifiez que vous avez bien remplacé votre ancien `agent.py`.

```cmd
pip install langgraph --upgrade
```

### 'source' n'est pas reconnu

**Cause** : vous utilisez la commande Linux sur Windows.  
**Solution** :
```cmd
venv\Scripts\activate
```

### AuthenticationError: Incorrect API key

**Cause** : clé OpenAI invalide ou expirée.  
**Solution** : générez une nouvelle clé sur https://platform.openai.com/api-keys

### RateLimitError

**Cause** : trop de requêtes ou crédit insuffisant.  
**Solution** : attendez quelques secondes ou rechargez du crédit sur https://platform.openai.com/usage

### L'app ne s'ouvre pas dans le navigateur

Ouvrez manuellement : **http://localhost:8501**

Pour changer le port :
```cmd
streamlit run app.py --server.port 8080
```

---

## 🏗️ Architecture technique

```
Utilisateur (navigateur)
        │
        ▼
   app.py (Streamlit)
   ├── Sidebar : préférences + clés API
   ├── Chat : affichage des messages
   └── Dashboard : métriques d'évaluation
        │
        ▼
   agent.py (TravelAgent)
   ├── LLM : ChatOpenAI (GPT-4o)
   ├── Agent : create_react_agent (LangGraph)
   └── Mémoire : MemorySaver (thread-based)
        │
        ▼
   tools.py (8 outils LangChain)
   ├── search_flights      → SerpAPI ou simulé
   ├── search_hotels       → SerpAPI ou simulé
   ├── search_activities   → Simulé
   ├── build_itinerary     → Générateur jour par jour
   ├── make_booking        → Confirmation simulée
   ├── get_weather_forecast → Météo simulée
   ├── convert_currency    → Taux de change statiques
   └── get_travel_advisory → Informations visa/santé
        │
        ▼
   metrics.py (TravelEvaluator) ← Totalement découplé
   ├── RetrievalMetrics    → Qualité des données récupérées
   ├── GenerationMetrics   → Qualité de la réponse
   ├── AgenticMetrics      → Comportement du pipeline
   └── LLMJudgeMetrics     → Évaluation qualitative GPT-4o-mini
```

---

## 📋 Checklist de démarrage

```
□ Clé OpenAI obtenue sur platform.openai.com
□ Dossier voyager_ai/ créé avec les 6 fichiers
□ Environnement virtuel créé : python -m venv venv
□ Environnement activé : venv\Scripts\activate
□ Dépendances installées : pip install -r requirements.txt
□ App lancée : streamlit run app.py
□ Clé OpenAI collée dans la sidebar
□ Premier message envoyé à l'agent
□ Tableau de bord de métriques consulté
```

---

*Voyager AI — Construit avec LangChain 1.x, LangGraph, Streamlit et OpenAI GPT-4o*
