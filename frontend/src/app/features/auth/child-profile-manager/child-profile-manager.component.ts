import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { UserCreateDto, UserResponse, UserRole } from '../../../core/models/user.model';
import { UserService } from '../../../core/services/user.service';

export interface ThemeOption {
  id: string;
  label: string;
  emoji: string;
  bgGradient: string;
  borderColor: string;
  badgeBg: string;
  badgeText: string;
  avatarBg: string;
  description: string;
}

export const THEME_OPTIONS: ThemeOption[] = [
  {
    id: 'Dinosaures',
    label: 'Dinosaures',
    emoji: '🦖',
    bgGradient: 'from-emerald-50 via-teal-50 to-green-100',
    borderColor: 'border-emerald-300 hover:border-emerald-500',
    badgeBg: 'bg-emerald-100',
    badgeText: 'text-emerald-800',
    avatarBg: 'bg-emerald-100 border-emerald-300',
    description: 'T-Rex, fossiles et volcans préhistoriques',
  },
  {
    id: 'Espace',
    label: 'Espace',
    emoji: '🚀',
    bgGradient: 'from-sky-50 via-blue-50 to-indigo-100',
    borderColor: 'border-sky-300 hover:border-sky-500',
    badgeBg: 'bg-sky-100',
    badgeText: 'text-sky-800',
    avatarBg: 'bg-sky-100 border-sky-300',
    description: 'Planètes, fusées et étoiles lointaines',
  },
  {
    id: 'Animaux',
    label: 'Animaux',
    emoji: '🦁',
    bgGradient: 'from-amber-50 via-yellow-50 to-orange-100',
    borderColor: 'border-amber-300 hover:border-amber-500',
    badgeBg: 'bg-amber-100',
    badgeText: 'text-amber-800',
    avatarBg: 'bg-amber-100 border-amber-300',
    description: 'Savane sauvage, jungle et océans',
  },
  {
    id: 'Magie',
    label: 'Magie',
    emoji: '🎨',
    bgGradient: 'from-purple-50 via-fuchsia-50 to-pink-100',
    borderColor: 'border-purple-300 hover:border-purple-500',
    badgeBg: 'bg-purple-100',
    badgeText: 'text-purple-800',
    avatarBg: 'bg-purple-100 border-purple-300',
    description: 'Sortilèges, créativité et contes enchantés',
  },
];

export const GRADE_LEVELS = [
  { value: '1ère primaire (CP)', label: '1ère année (CP - 6 ans)' },
  { value: '2ème primaire (CE1)', label: '2ème année (CE1 - 7 ans)' },
  { value: '3ème primaire (CE2)', label: '3ème année (CE2 - 8 ans)' },
  { value: '4ème primaire (CM1)', label: '4ème année (CM1 - 9 ans)' },
  { value: '5ème primaire (CM2)', label: '5ème année (CM2 - 10 ans)' },
  { value: '6ème primaire (6ème)', label: '6ème année (6ème - 11 ans)' },
];

@Component({
  selector: 'app-child-profile-manager',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './child-profile-manager.component.html',
})
export class ChildProfileManagerComponent implements OnInit {
  private readonly userService = inject(UserService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  // --- Constantes exposées au template ---
  readonly themes = THEME_OPTIONS;
  readonly gradeLevels = GRADE_LEVELS;

  // --- Angular Signals : Gestion d'état réactive ---
  readonly children = signal<UserResponse[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly isSubmitting = signal<boolean>(false);
  readonly isDeleting = signal<boolean>(false);
  readonly feedbackMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);
  readonly childToDelete = signal<UserResponse | null>(null);
  readonly selectedGradeFilter = signal<string>('ALL');

  // --- Computed Signals ---
  readonly totalChildren = computed(() => this.children().length);
  readonly hasChildren = computed(() => this.children().length > 0);
  readonly filteredChildren = computed(() => {
    const filter = this.selectedGradeFilter();
    if (filter === 'ALL') {
      return this.children();
    }
    return this.children().filter((child) => child.grade_level === filter);
  });

  // --- Formulaire Réactif ---
  readonly profileForm = this.fb.nonNullable.group({
    username: [
      '',
      [Validators.required, Validators.minLength(3), Validators.maxLength(30)],
    ],
    age: [
      7,
      [Validators.required, Validators.min(5), Validators.max(14)],
    ],
    grade_level: [
      '2ème primaire (CE1)',
      [Validators.required],
    ],
    favorite_theme: [
      'Dinosaures',
      [Validators.required],
    ],
  });

  ngOnInit(): void {
    this.loadChildren();
  }

  /**
   * Charge la liste des profils enfants depuis le backend FastAPI.
   */
  loadChildren(): void {
    this.isLoading.set(true);
    this.userService.getChildren().subscribe({
      next: (data: UserResponse[]) => {
        this.children.set(data);
        this.isLoading.set(false);
      },
      error: (err: Error) => {
        this.isLoading.set(false);
        this.showFeedback('error', err.message || 'Impossible de charger les profils.');
      },
    });
  }

  /**
   * Sélectionne un thème visuel depuis la liste des cartes radio.
   */
  selectTheme(themeId: string): void {
    this.profileForm.patchValue({ favorite_theme: themeId });
    this.profileForm.get('favorite_theme')?.markAsDirty();
  }

  onGradeFilterChange(event: Event): void {
    const select = event.target;
    if (select instanceof HTMLSelectElement) {
      this.selectedGradeFilter.set(select.value);
    }
  }

  /**
   * Soumission du formulaire d'inscription enfant.
   */
  onSubmit(): void {
    this.profileForm.controls.username.setValue(this.profileForm.controls.username.value.trim());
    if (this.profileForm.invalid) {
      this.profileForm.markAllAsTouched();
      this.showFeedback('error', 'Oups ! Merci de corriger les informations en rouge.');
      return;
    }

    this.isSubmitting.set(true);
    const formVal = this.profileForm.getRawValue();

    // Les identifiants techniques sont uniques et ne sont pas affichés aux enfants.
    const sanitizedUsername = (formVal.username ?? '').trim().toLowerCase().replace(/[^a-z0-9]/g, '');
    const randomSuffix = crypto.randomUUID().replace(/-/g, '').slice(0, 10);
    const email = `${sanitizedUsername || 'aventurier'}_${randomSuffix}@kid.edugenius.ai`;

    const dto: UserCreateDto = {
      username: (formVal.username ?? '').trim(),
      email,
      password: `${crypto.randomUUID()}A1!`,
      role: UserRole.CHILD,
      age: formVal.age,
      grade_level: formVal.grade_level,
      favorite_theme: formVal.favorite_theme,
    };

    this.userService.createChildProfile(dto).subscribe({
      next: (createdChild: UserResponse) => {
        this.profileForm.reset({
          username: '',
          age: 7,
          grade_level: '2ème primaire (CE1)',
          favorite_theme: 'Dinosaures',
        });
        this.isSubmitting.set(false);
        this.showFeedback(
          'success',
          `🎉 Youpi ! Le profil de ${createdChild.username} a été créé avec succès !`
        );
        this.loadChildren();
      },
      error: (err: Error) => {
        this.isSubmitting.set(false);
        this.showFeedback('error', err.message || 'Erreur lors de la création du profil.');
      },
    });
  }

  /**
   * Ouvre la modale de confirmation avant suppression.
   */
  openDeleteModal(child: UserResponse): void {
    this.childToDelete.set(child);
  }

  /**
   * Ferme la modale de confirmation.
   */
  closeDeleteModal(): void {
    if (!this.isDeleting()) {
      this.childToDelete.set(null);
    }
  }

  /**
   * Confirme et exécute la suppression définitive du profil.
   */
  confirmDelete(): void {
    const target = this.childToDelete();
    if (!target) return;

    this.isDeleting.set(true);
    this.userService.delete(target.id).subscribe({
      next: () => {
        this.children.update((list) => list.filter((c) => c.id !== target.id));
        this.isDeleting.set(false);
        this.childToDelete.set(null);
        this.showFeedback('success', `Le profil de ${target.username} a été supprimé.`);
      },
      error: (err: Error) => {
        this.isDeleting.set(false);
        this.showFeedback('error', err.message || 'Impossible de supprimer ce profil.');
      },
    });
  }

  /**
   * Ouvre la page d'accueil de l'enfant sélectionné.
   */
  launch(child: UserResponse): void {
    this.router.navigate(['/home', child.id]);
  }

  /**
   * Retourne la configuration visuelle associée au thème choisi.
   */
  getThemeConfig(themeName?: string | null): ThemeOption {
    const match = this.themes.find((t) => t.id === themeName);
    return (
      match || {
        id: 'Default',
        label: themeName || 'Aventure',
        emoji: '🧒',
        bgGradient: 'from-sky-50 to-blue-100',
        borderColor: 'border-sky-300',
        badgeBg: 'bg-sky-100',
        badgeText: 'text-sky-800',
        avatarBg: 'bg-sky-100 border-sky-300',
        description: 'Parcours d’apprentissage',
      }
    );
  }

  /**
   * Affiche un message de feedback avec disparition automatique.
   */
  private showFeedback(type: 'success' | 'error', text: string): void {
    this.feedbackMessage.set({ type, text });
    setTimeout(() => {
      if (this.feedbackMessage()?.text === text) {
        this.feedbackMessage.set(null);
      }
    }, 4500);
  }

  dismissFeedback(): void {
    this.feedbackMessage.set(null);
  }
}
