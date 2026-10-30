# 🎨 EduGenius AI (Kids Edition) - Frontend Design System & Style Guide

Bienvenue dans le guide de style et de conception frontend pour **EduGenius AI**.
Ce document rassemble **toutes les conventions graphiques, tokens Tailwind, typographies et bonnes pratiques Angular 18** pour garantir une expérience utilisateur cohérente, magique et adaptée aux enfants sur l'ensemble des modules (`auth`, `lessons`, `tutor`, `quiz-playground`, `visual-studio`).

---

## 🌈 1. Palette de Couleurs "Kids Theme"

Toutes ces couleurs sont configurées dans `tailwind.config.js` sous le préfixe `kids-`. Utilisez toujours ces classes plutôt que des couleurs brutes !

### Couleurs Principales & Rôles Sémantiques

| Token Tailwind | Code HEX | Rendu / Teinte | Utilisation dans l'interface |
| :--- | :--- | :--- | :--- |
| `kids-primary` | `#38BDF8` | 🟦 Bleu ciel éclatant | **Action principale**, barre de navigation, boutons héros, liens actifs |
| `kids-primary.light` | `#BAE6FD` | 🧊 Bleu pastel très doux | Bordures de cartes, arrière-plans de badges clairs, icônes |
| `kids-primary.dark` | `#0284C7` | 🌊 Bleu océan profond | Bordures 3D sous les boutons, texte accentué |
| `kids-secondary` | `#FBBF24` | 🟨 Jaune soleil radieux | **Récompenses**, étoiles de score, badges de points, boutons d'action ludiques |
| `kids-secondary.light`| `#FEF08A` | 🐣 Jaune poussin délicat | Puces de catégorie, surbrillances |
| `kids-secondary.dark` | `#D97706` | 🍯 Ambre doré | Bordures 3D des boutons secondaires |
| `kids-success` | `#34D399` | 🟩 Vert prairie pétillant | **Bonnes réponses**, validation d'exercices, barre de progression |
| `kids-success.light` | `#A7F3D0` | 🌿 Menthe pastel | Fond des bannières de succès, coches de validation |
| `kids-success.dark` | `#059669` | 🌲 Vert forêt | Bordures 3D des boutons succès |
| `kids-accent.coral` | `#FB7185` | 🪸 Corail dynamique | Actions d'alerte, boutons d'enregistrement micro, défis chronométrés |
| `kids-accent.purple`| `#A78BFA` | 🔮 Lilas magique | Cours de créativité/français, assistant IA magicien |
| `kids-accent.orange`| `#FB923C` | 🍊 Orange mandarine | Badges d'aventure, découvertes, indices |
| `kids-dark` | `#1E293B` | 🕶️ Ardoise très foncée | **Texte principal** (jamais de noir pur `#000000`, trop agressif pour les yeux) |
| `kids-dark.muted` | `#64748B` | 🌫️ Ardoise adoucie | Textes secondaires, consignes d'aide, dates, sous-titres |
| `kids-surface.soft` | `#F8FAFC` | ☁️ Blanc bleuté nuage | **Arrière-plan global des pages** (`bg-kids-surface-soft`) |
| `kids-surface.card` | `#F0F9FF` | 🕊️ Blanc bleuté très pâle | Arrière-plan des conteneurs légers ou encarts |

### Couleurs des 4 Thèmes d'Apprentissage

| Thème | Emoji | Token Tailwind | Couleur | Utilisation |
| :--- | :---: | :--- | :--- | :--- |
| **Dinosaures** | 🦖 | `kids-themes.dino` | `#10B981` (Émeraude) | Sciences naturelles, géologie, histoire ancienne |
| **Espace** | 🚀 | `kids-themes.space`| `#6366F1` (Indigo) | Astronomie, physique, mathématiques spatiales |
| **Animaux** | 🦁 | `kids-themes.nature`| `#F59E0B` (Miel/Ambre) | Biodiversité, géographie, écologie |
| **Magie & Art** | 🎨 | `kids-accent.purple`| `#A78BFA` (Violet) | Dessin, langues, littérature, contes |

---

## 🔤 2. Typographie & Polices

Nous utilisons deux polices Google Fonts gratuites, importées globalement dans `src/styles.scss` :

1. **`font-kids` (Fredoka)** : Police ronde, joviale et géométrique.
   - **Usage :** Titres (`h1` à `h4`), gros boutons, scores, badges, cartes d'exercices.
   - **Pourquoi :** Formes douces très faciles à décoder pour les enfants de 6 à 12 ans.
2. **`font-body` (Nunito)** : Police lisible, humaniste et bienveillante.
   - **Usage :** Paragraphes, résumés de cours (`summary_kid`), questions de quiz, formulaires.

### Hiérarchie des Titres Recommandée

```html
<!-- Titre de Page (Écran d'accueil / Module) -->
<h1 class="text-3xl md:text-4xl font-kids font-bold text-kids-dark tracking-tight">
  🌟 Mon Chapitre Magique
</h1>

<!-- Titre de Section ou de Carte -->
<h2 class="text-2xl font-kids font-bold text-kids-dark">
  🚀 Les Mystères du Système Solaire
</h2>

<!-- Sous-titre ou Question d'exercice -->
<h3 class="text-xl font-kids font-semibold text-kids-dark">
  Quelle est la plus grande planète ?
</h3>

<!-- Corps de texte / Explication enfant -->
<p class="text-base md:text-lg font-body font-medium text-kids-dark leading-relaxed">
  Jupiter est une planète géante gazeuse. Elle est si grande qu'on pourrait y glisser toutes les autres planètes !
</p>
```

---

## 🔘 3. Composants CSS Prêts à l'Emploi

Ces classes sont déclarées dans `src/styles.scss` et peuvent être appliquées directement dans vos templates HTML :

### 1. Boutons Rebondissants 3D ("Bouncy Buttons")

Boutons avec effet de volume cartoon et micro-interaction tactile au clic (`active:translate-y-1`) :

```html
<!-- Bouton Principal (Bleu Ciel) -->
<button class="btn-kids-primary">
  <span>🚀 C'est parti !</span>
</button>

<!-- Bouton Secondaire (Jaune Soleil / Or) -->
<button class="btn-kids-secondary">
  <span>⭐ Voir mes récompenses</span>
</button>

<!-- Bouton Accent / Alerte (Corail Rose) -->
<button class="btn-kids-accent">
  <span>🎙️ Enregistrer ma voix</span>
</button>

<!-- Bouton Validation / Réponse (Vert Prairie) -->
<button class="btn-kids-success">
  <span>✅ Valider ma réponse</span>
</button>
```

### 2. Cartes d'Apprentissage Flottantes (`card-kids`)

Cartes blanches aux coins très arrondis (`rounded-3xl`), bordure douce et ombre flottante au survol :

```html
<div class="card-kids">
  <div class="flex items-center gap-4">
    <div class="w-16 h-16 rounded-2xl bg-kids-primary-light flex items-center justify-center text-3xl shadow-inner">
      🪐
    </div>
    <div>
      <h3 class="text-xl font-kids font-bold text-kids-dark">La Planète Saturne</h3>
      <p class="text-sm text-kids-dark-muted font-medium">Découvre ses anneaux scintillants</p>
    </div>
  </div>
</div>
```

### 3. Badges Ludo-Éducatifs (`badge-kids`)

Puces arrondies pour afficher la classe, la matière ou la difficulté :

```html
<span class="badge-kids bg-emerald-100 text-emerald-800">
  🌿 Niveau CE2
</span>

<span class="badge-kids bg-amber-100 text-amber-800">
  ⭐ 150 Étoiles
</span>

<span class="badge-kids bg-sky-100 text-sky-800">
  📚 Sciences & Découverte
</span>
```

---

## 📐 4. Règles Graphiques Incontournables pour les Enfants

1. **Arrondis généreux :**
   - **Toujours :** `rounded-3xl` pour les conteneurs/cartes, `rounded-2xl` pour les inputs, `rounded-full` pour les boutons et badges.
   - **Jamais :** d'angles droits stricts (`rounded-none` ou `rounded-sm`).
2. **Micro-animations tactiles :**
   - Ajoutez systématiquement `hover:scale-105 active:scale-95 transition-transform duration-200` sur les éléments cliquables.
3. **Ombres douces et colorées :**
   - Utilisez `shadow-kids-card`, `shadow-kids-soft` ou `shadow-kids-floating`.
4. **Langage visuel riche :**
   - Utilisez de grands émojis (taille `text-3xl` à `text-5xl`) pour guider les jeunes enfants qui apprennent à lire.

---

## 💻 5. Modèle Architectural Angular 18

Pour que notre code reste propre et homogène, appliquez ce modèle dans tous les nouveaux composants :

### Template d'un Composant Standalone Moderne

```typescript
import { Component, computed, inject, signal, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';
// Importer les services depuis core
import { CourseService } from '../../../core/services/course.service';
import { CourseResponse } from '../../../core/models/course.model';

@Component({
  selector: 'app-lesson-explorer',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './lesson-explorer.component.html',
})
export class LessonExplorerComponent implements OnInit {
  // 1. Injection moderne Angular 18 (pas de constructeur lourd)
  private readonly courseService = inject(CourseService);

  // 2. Gestion d'état avec les Signals Angular (pas de variables muables non réactives)
  readonly courses = signal<CourseResponse[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly selectedTheme = signal<string>('ALL');

  // 3. Valeurs calculées réactives (computed)
  readonly totalCourses = computed(() => this.courses().length);
  readonly hasCourses = computed(() => this.courses().length > 0);

  ngOnInit(): void {
    this.loadCourses();
  }

  loadCourses(): void {
    this.isLoading.set(true);
    this.courseService.getAll().subscribe({
      next: (data) => {
        this.courses.set(data);
        this.isLoading.set(false);
      },
      error: () => this.isLoading.set(false),
    });
  }
}
```

---

## 📁 6. Emplacement des Fichiers Clés

- **Configuration des couleurs et ombres :** [`frontend/tailwind.config.js`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/tailwind.config.js)
- **Directives CSS et composants globaux :** [`frontend/src/styles.scss`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/styles.scss)
- **Modèles de données partagés :**
  - Utilisateurs / Enfants : [`frontend/src/app/core/models/user.model.ts`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/app/core/models/user.model.ts)
  - Cours / Chapitres : [`frontend/src/app/core/models/course.model.ts`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/app/core/models/course.model.ts)
- **Services HTTP partagés :**
  - [`frontend/src/app/core/services/user.service.ts`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/app/core/services/user.service.ts)
  - [`frontend/src/app/core/services/course.service.ts`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/app/core/services/course.service.ts)
- **Exemple de référence UI complète :**
  - [`frontend/src/app/features/auth/child-profile-manager/child-profile-manager.component.html`](file:///c:/Users/Administrateur/Desktop/My%20projects/edugenius-ai/frontend/src/app/features/auth/child-profile-manager/child-profile-manager.component.html)
