import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { UserCreateDto, UserResponse, UserRole } from '../../../core/models/user.model';
import { UserPublic } from '../../../core/models/auth.model';
import { AuthService } from '../../../core/services/auth.service';
import { ChildSessionService } from '../../../core/services/child-session.service';
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
  { value: '1ère primaire (CP)', label: 'CP (6 ans)' },
  { value: '2ème primaire (CE1)', label: 'CE1 (7 ans)' },
  { value: '3ème primaire (CE2)', label: 'CE2 (8 ans)' },
  { value: '4ème primaire (CM1)', label: 'CM1 (9 ans)' },
  { value: '5ème primaire (CM2)', label: 'CM2 (10 ans)' },
  { value: '6ème primaire (6ème)', label: '6ème (11 ans)' },
];

@Component({
  selector: 'app-parent-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './parent-dashboard.component.html',
})
export class ParentDashboardComponent implements OnInit {
  private readonly userService = inject(UserService);
  private readonly authService = inject(AuthService);
  private readonly childSessionService = inject(ChildSessionService);
  private readonly fb = inject(FormBuilder);
  private readonly router = inject(Router);

  // Constantes exposées au template
  readonly themes = THEME_OPTIONS;
  readonly gradeLevels = GRADE_LEVELS;

  // Signals réactifs d'état
  readonly children = signal<UserResponse[]>([]);
  readonly isLoading = signal<boolean>(false);
  readonly isSubmitting = signal<boolean>(false);
  readonly isDeleting = signal<boolean>(false);
  readonly isAddModalOpen = signal<boolean>(false);
  readonly feedbackMessage = signal<{ type: 'success' | 'error'; text: string } | null>(null);

  // Modales d'interaction
  readonly childToDelete = signal<UserResponse | null>(null);
  readonly childToEdit = signal<UserResponse | null>(null);
  readonly previewChildProgress = signal<UserResponse | null>(null);

  // Parent connecté
  readonly parentName = computed(() => {
    const user = this.authService.currentUser();
    return user ? user.username : 'Parent';
  });

  readonly hasChildren = computed(() => this.children().length > 0);

  // Formulaire d'ajout d'enfant
  readonly childForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    age: [8, [Validators.required, Validators.min(4), Validators.max(15)]],
    grade_level: ['3ème primaire (CE2)', [Validators.required]],
    favorite_theme: ['Dinosaures', [Validators.required]],
  });

  // Formulaire de modification d'enfant
  readonly editChildForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(2), Validators.maxLength(50)]],
    age: [8, [Validators.required, Validators.min(4), Validators.max(15)]],
    grade_level: ['3ème primaire (CE2)', [Validators.required]],
    favorite_theme: ['Dinosaures', [Validators.required]],
  });

  ngOnInit(): void {
    this.loadChildren();
  }

  loadChildren(): void {
    this.isLoading.set(true);
    this.userService.getMyChildren().subscribe({
      next: (data) => {
        this.children.set(data);
        this.isLoading.set(false);
        // Restauration de l'enfant actif si déjà sélectionné
        this.childSessionService.restoreActiveChild(data as UserPublic[]);
      },
      error: (err: Error) => {
        this.isLoading.set(false);
        this.showFeedback('error', err.message || 'Impossible de charger vos profils enfants.');
      },
    });
  }

  // --- Gestion du formulaire modal ---
  openAddModal(): void {
    this.childForm.reset({
      username: '',
      age: 8,
      grade_level: '3ème primaire (CE2)',
      favorite_theme: 'Dinosaures',
    });
    this.isAddModalOpen.set(true);
  }

  closeAddModal(): void {
    this.isAddModalOpen.set(false);
  }

  selectTheme(themeId: string): void {
    this.childForm.patchValue({ favorite_theme: themeId });
  }

  submitAddChild(): void {
    if (this.childForm.invalid) {
      this.childForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    const formVal = this.childForm.getRawValue();

    const dto: UserCreateDto = {
      username: formVal.username.trim(),
      role: UserRole.CHILD,
      age: formVal.age,
      grade_level: formVal.grade_level,
      favorite_theme: formVal.favorite_theme,
    };

    this.userService.createChild(dto).subscribe({
      next: (createdChild) => {
        this.isSubmitting.set(false);
        this.closeAddModal();
        this.children.update((list) => [...list, createdChild]);
        this.showFeedback('success', `L’aventurier ${createdChild.username} a été ajouté avec succès !`);
      },
      error: (err: Error) => {
        this.isSubmitting.set(false);
        this.showFeedback('error', err.message || 'Erreur lors de la création du profil enfant.');
      },
    });
  }

  // --- Gestion du formulaire modal de modification ---
  openEditModal(child: UserResponse): void {
    this.childToEdit.set(child);
    this.editChildForm.reset({
      username: child.username,
      age: child.age ?? 8,
      grade_level: child.grade_level ?? '3ème primaire (CE2)',
      favorite_theme: child.favorite_theme ?? 'Dinosaures',
    });
  }

  closeEditModal(): void {
    this.childToEdit.set(null);
  }

  selectEditTheme(themeId: string): void {
    this.editChildForm.patchValue({ favorite_theme: themeId });
  }

  submitEditChild(): void {
    const target = this.childToEdit();
    if (!target) return;

    if (this.editChildForm.invalid) {
      this.editChildForm.markAllAsTouched();
      return;
    }

    this.isSubmitting.set(true);
    const formVal = this.editChildForm.getRawValue();

    const dto: Partial<UserCreateDto> = {
      username: formVal.username.trim(),
      age: formVal.age,
      grade_level: formVal.grade_level,
      favorite_theme: formVal.favorite_theme,
    };

    this.userService.updateChild(target.id, dto).subscribe({
      next: (updatedChild) => {
        this.isSubmitting.set(false);
        this.closeEditModal();

        // Mise à jour réactive de la liste d'enfants
        this.children.update((list) =>
          list.map((c) => (c.id === updatedChild.id ? updatedChild : c))
        );

        // Si l'enfant modifié est celui en cours de session active, synchroniser la session
        if (this.childSessionService.activeChild()?.id === updatedChild.id) {
          this.childSessionService.selectChild(updatedChild as UserPublic);
        }

        this.showFeedback(
          'success',
          `Le profil de ${updatedChild.username} a été mis à jour avec succès !`
        );
      },
      error: (err: Error) => {
        this.isSubmitting.set(false);
        this.showFeedback('error', err.message || 'Erreur lors de la modification du profil.');
      },
    });
  }

  // --- Lancement de l'aventure enfant ---
  launchAdventure(child: UserResponse): void {
    this.childSessionService.selectChild(child as UserPublic);
    this.router.navigate(['/home', child.id]);
  }

  // --- Aperçu et suivi des progrès ---
  openProgressPreview(child: UserResponse): void {
    this.childSessionService.selectChild(child as UserPublic);
    this.previewChildProgress.set(child);
  }

  closeProgressPreview(): void {
    this.previewChildProgress.set(null);
  }

  goToFullProgress(child: UserResponse): void {
    this.childSessionService.selectChild(child as UserPublic);
    this.closeProgressPreview();
    this.router.navigate(['/progress'], { queryParams: { child: child.id } });
  }

  // --- Suppression sécurisée ---
  openDeleteModal(child: UserResponse): void {
    this.childToDelete.set(child);
  }

  closeDeleteModal(): void {
    this.childToDelete.set(null);
  }

  confirmDelete(): void {
    const target = this.childToDelete();
    if (!target) return;

    this.isDeleting.set(true);
    this.userService.delete(target.id).subscribe({
      next: () => {
        this.isDeleting.set(false);
        this.children.update((list) => list.filter((c) => c.id !== target.id));
        if (this.childSessionService.activeChild()?.id === target.id) {
          this.childSessionService.clearActiveChild();
        }
        this.closeDeleteModal();
        this.showFeedback('success', `Le profil de ${target.username} a été supprimé.`);
      },
      error: (err: Error) => {
        this.isDeleting.set(false);
        this.showFeedback('error', err.message || 'Erreur lors de la suppression.');
      },
    });
  }

  getThemeConfig(themeName?: string | null): ThemeOption {
    return (
      this.themes.find((t) => t.id === themeName) || {
        id: 'Dinosaures',
        label: 'Dinosaures',
        emoji: '🦖',
        bgGradient: 'from-emerald-50 via-teal-50 to-green-100',
        borderColor: 'border-emerald-300 hover:border-emerald-500',
        badgeBg: 'bg-emerald-100',
        badgeText: 'text-emerald-800',
        avatarBg: 'bg-emerald-100 border-emerald-300',
        description: 'Parcours d’aventure',
      }
    );
  }

  private showFeedback(type: 'success' | 'error', text: string): void {
    this.feedbackMessage.set({ type, text });
    setTimeout(() => {
      if (this.feedbackMessage()?.text === text) {
        this.feedbackMessage.set(null);
      }
    }, 4500);
  }
}
