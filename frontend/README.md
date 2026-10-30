# 🎨 EduGenius AI - Frontend (Kids Edition)

Application frontend ludo-éducative pour enfants développée avec **Angular 18+ (Standalone Components)** et **Tailwind CSS**.

---

## 📖 Guide de Style & Design System pour l'Équipe

👉 **Consultez impérativement le document : [`DESIGN_SYSTEM.md`](./DESIGN_SYSTEM.md)** avant de coder vos écrans !
Il contient :
- La palette de couleurs officielle (`kids-primary`, `kids-secondary`, `kids-accent`, etc.).
- Les typographies adaptées aux enfants (`font-kids` Fredoka et `font-body` Nunito).
- Les classes CSS réutilisables (`.btn-kids-primary`, `.card-kids`, `.badge-kids`).
- Les patterns Angular 18 (Signals, `inject(HttpClient)`, formulaires réactifs).

---

## 🚀 Démarrage Rapide

### 1. Installation des dépendances
```bash
npm install
```

### 2. Lancer le serveur de développement
```bash
npm start
```
L'application sera accessible sur [http://localhost:4200/](http://localhost:4200/).

### 3. Exécuter les tests unitaires
```bash
npm test -- --watch=false
```

### 4. Compiler pour la production
```bash
npm run build
```
Le bundle optimisé sera généré dans `dist/frontend`.

---

## 🧱 Architecture du Projet

```text
src/app/
├── core/                   # Cœur applicatif partagé
│   ├── guards/             # Gardes de navigation
│   ├── interceptors/       # Intercepteurs HTTP
│   ├── models/             # Interfaces & DTOs TypeScript (user.model.ts, course.model.ts)
│   └── services/           # Services HTTP (user.service.ts, course.service.ts)
├── features/               # Modules fonctionnels par équipe
│   ├── auth/               # Module 1 : Authentification & Gestion des profils enfants
│   ├── lessons/            # Module 2 : Résumés de cours & Flashcards
│   ├── tutor/              # Module 3 : Compagnon tuteur IA
│   ├── quiz-playground/    # Module 4 : Quiz & Analyse des progrès
│   └── visual-studio/      # Module 5 : Schémas & Vidéos explicatives
└── shared/                 # Composants et pipes partagés
```
