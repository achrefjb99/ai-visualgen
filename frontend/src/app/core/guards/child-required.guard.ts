/**
 * Garde de navigation fonctionnel Angular 18 (Module 1).
 * Empêche l'accès aux activités d'apprentissage si aucun enfant n'est sélectionné.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { ChildSessionService } from '../services/child-session.service';

export const childRequiredGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const childSessionService = inject(ChildSessionService);
  const router = inject(Router);

  if (childSessionService.hasActiveChild()) {
    return true;
  }

  // Redirection vers le tableau de bord parent si aucun enfant n'est sélectionné
  return router.createUrlTree(['/parent-dashboard'], {
    queryParams: { returnUrl: state.url },
  });
};
