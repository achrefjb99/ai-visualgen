/**
 * Service de gestion de la session de l'enfant actif (Module 1).
 * Gère l'état global réactif via Angular 18 Signals et la persistance locale.
 */

import { computed, Injectable, signal } from '@angular/core';
import { UserPublic } from '../models/auth.model';

export const ACTIVE_CHILD_STORAGE_KEY = 'edugenius_active_child_id';

@Injectable({
  providedIn: 'root',
})
export class ChildSessionService {
  // --- Propriétés réactives (Signals) ---
  readonly activeChild = signal<UserPublic | null>(null);
  readonly hasActiveChild = computed<boolean>(() => !!this.activeChild());
  readonly activeTheme = computed<string>(
    () => this.activeChild()?.favorite_theme || 'space'
  );
  readonly activeGrade = computed<string>(
    () => this.activeChild()?.grade_level || 'CE2'
  );

  /**
   * Sélectionne un enfant actif et persiste son identifiant dans le localStorage.
   */
  selectChild(child: UserPublic): void {
    this.activeChild.set(child);
    try {
      localStorage.setItem(ACTIVE_CHILD_STORAGE_KEY, child.id.toString());
    } catch {
      // Ignorer si localStorage est inaccessible
    }
  }

  /**
   * Réinitialise la session enfant pour revenir à l'espace de supervision parent.
   */
  clearActiveChild(): void {
    this.activeChild.set(null);
    try {
      localStorage.removeItem(ACTIVE_CHILD_STORAGE_KEY);
    } catch {
      // Ignorer
    }
  }

  /**
   * Restaure l'enfant actif depuis le localStorage à partir d'une liste d'enfants fournie.
   */
  restoreActiveChild(childrenList: UserPublic[]): void {
    if (!childrenList || childrenList.length === 0) {
      return;
    }

    const savedId = this.getActiveChildId();
    if (!savedId) {
      return;
    }

    const matchedChild = childrenList.find((c) => c.id === savedId);
    if (matchedChild) {
      this.activeChild.set(matchedChild);
    } else {
      // Nettoyage si l'identifiant stocké ne correspond plus à aucun enfant valide
      this.clearActiveChild();
    }
  }

  /**
   * Récupère l'identifiant numérique de l'enfant actif stocké dans le localStorage.
   */
  getActiveChildId(): number | null {
    try {
      const val = localStorage.getItem(ACTIVE_CHILD_STORAGE_KEY);
      return val ? parseInt(val, 10) : null;
    } catch {
      return null;
    }
  }
}
