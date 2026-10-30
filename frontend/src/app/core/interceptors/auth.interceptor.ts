/**
 * Intercepteur HTTP fonctionnel Angular 18 (Module 1).
 * Injecte automatiquement le Bearer Token JWT et intercepte les erreurs 401 Unauthorized.
 */

import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { AuthService } from '../services/auth.service';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const router = inject(Router);

  const token = authService.getToken();
  const isApiRequest = req.url.startsWith(environment.apiUrl) || req.url.includes('/api/v1');

  let authReq = req;
  if (token && isApiRequest) {
    authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`,
      },
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // Déconnexion automatique et redirection si la session est expirée/invalide
      // Ne pas rediriger si la requête elle-même est la tentative de login
      const isLoginRequest = req.url.includes('/auth/login') || req.url.includes('/auth/token');

      if (error.status === 401 && !isLoginRequest) {
        authService.logout();
        router.navigate(['/login']);
      }

      return throwError(() => error);
    })
  );
};
