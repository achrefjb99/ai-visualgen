/**
 * Service central d'authentification et de gestion de session JWT (Module 1).
 * Utilise l'injection moderne d'Angular 18 et les Signals réactifs.
 */

import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { computed, inject, Injectable, signal } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import { LoginRequest, RegisterRequest, TokenResponse, UserPublic } from '../models/auth.model';

export const AUTH_TOKEN_KEY = 'edugenius_token';

@Injectable({
  providedIn: 'root',
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);

  private readonly authUrl = `${environment.apiUrl.replace(/\/+$/, '')}/auth`;

  // --- Angular Signals : État réactif de session ---
  readonly currentUser = signal<UserPublic | null>(null);
  readonly isAuthenticated = computed(() => !!this.currentUser());
  readonly isCheckingSession = signal<boolean>(false);

  constructor() {
    // Restauration automatique de session au démarrage si un jeton est présent
    if (this.getToken()) {
      this.checkSession().subscribe();
    }
  }

  /**
   * Récupère le jeton JWT persisté dans le localStorage.
   */
  getToken(): string | null {
    try {
      return localStorage.getItem(AUTH_TOKEN_KEY);
    } catch {
      return null;
    }
  }

  /**
   * Authentifie un utilisateur avec ses identifiants.
   * Stocke le jeton JWT et met à jour l'utilisateur courant.
   */
  login(credentials: LoginRequest): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${this.authUrl}/login`, credentials)
      .pipe(
        tap((response) => {
          this.setToken(response.access_token);
          this.currentUser.set(response.user);
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => error);
        })
      );
  }

  /**
   * Inscrit un nouvel utilisateur (Parent ou Enseignant).
   * Stocke immédiatement le jeton JWT et connecte l'utilisateur.
   */
  register(dto: RegisterRequest): Observable<TokenResponse> {
    return this.http
      .post<TokenResponse>(`${this.authUrl}/register`, dto)
      .pipe(
        tap((response) => {
          this.setToken(response.access_token);
          this.currentUser.set(response.user);
        }),
        catchError((error: HttpErrorResponse) => {
          return throwError(() => error);
        })
      );
  }

  /**
   * Vérifie et restaure la session active auprès du backend (/api/v1/auth/me).
   * Retourne l'utilisateur connecté ou null si le jeton est inexistant ou révoqué.
   */
  checkSession(): Observable<UserPublic | null> {
    const token = this.getToken();
    if (!token) {
      this.currentUser.set(null);
      return of(null);
    }

    this.isCheckingSession.set(true);
    return this.http.get<UserPublic>(`${this.authUrl}/me`).pipe(
      tap((user) => {
        this.currentUser.set(user);
        this.isCheckingSession.set(false);
      }),
      catchError(() => {
        this.clearSession();
        this.isCheckingSession.set(false);
        return of(null);
      })
    );
  }

  /**
   * Déconnecte l'utilisateur, supprime le jeton et redirige vers /login.
   */
  logout(): void {
    this.clearSession();
    this.router.navigate(['/login']);
  }

  /**
   * Enregistre le jeton JWT dans le localStorage.
   */
  private setToken(token: string): void {
    try {
      localStorage.setItem(AUTH_TOKEN_KEY, token);
    } catch {
      // Ignorer les erreurs d'accès à localStorage (ex: mode navigation privée stricte)
    }
  }

  /**
   * Réinitialise l'état local et vide le stockage.
   */
  private clearSession(): void {
    try {
      localStorage.removeItem(AUTH_TOKEN_KEY);
    } catch {
      // Ignorer
    }
    this.currentUser.set(null);
  }
}
