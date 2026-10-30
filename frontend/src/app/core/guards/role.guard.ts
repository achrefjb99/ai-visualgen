/**
 * Garde de navigation fonctionnel basé sur les rôles (Angular 18).
 * Vérifie que l'utilisateur connecté possède l'un des rôles autorisés (route.data['roles']).
 */

import { inject } from '@angular/core';
import { CanActivateFn, Router, UrlTree } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { UserRole } from '../models/auth.model';

export const roleGuard: CanActivateFn = (route, state): boolean | UrlTree => {
  const authService = inject(AuthService);
  const router = inject(Router);

  if (!authService.isAuthenticated()) {
    return router.createUrlTree(['/login'], {
      queryParams: { returnUrl: state.url },
    });
  }

  const expectedRoles = route.data?.['roles'] as UserRole[] | undefined;
  if (!expectedRoles || expectedRoles.length === 0) {
    return true;
  }

  const currentRole = authService.currentUser()?.role;
  if (currentRole && expectedRoles.includes(currentRole)) {
    return true;
  }

  // Redirection contextuelle si le rôle ne correspond pas
  if (currentRole === UserRole.TEACHER) {
    return router.createUrlTree(['/teacher-dashboard']);
  }
  return router.createUrlTree(['/parent-dashboard']);
};
