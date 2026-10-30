/**
 * Garde de navigation fonctionnel Angular 18 (Module 1).
 * Protège l'accès aux routes privées en vérifiant l'état d'authentification.
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

export const authGuard: CanActivateFn = (route, state) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (authService.isAuthenticated()) {
    return true;
  }

  // Redirection vers /login avec conservation de l'URL demandée pour redirection ultérieure
  return router.createUrlTree(['/login'], {
    queryParams: { returnUrl: state.url },
  });
};
