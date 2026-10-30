/**
 * Service Angular de gestion des utilisateurs et profils enfants.
 * Utilise l'injection moderne Angular 18 et la gestion réactive RxJS.
 */

import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import {
  UserCreateDto,
  UserFilterParams,
  UserResponse,
  UserRole,
  UserUpdateDto,
} from '../models/user.model';

@Injectable({
  providedIn: 'root',
})
export class UserService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = `${environment.apiUrl.replace(/\/+$/, '')}/users`;

  /**
   * Récupère la liste paginée des utilisateurs avec filtres optionnels.
   */
  getAll(filterParams?: UserFilterParams): Observable<UserResponse[]> {
    let params = new HttpParams();

    if (filterParams) {
      if (filterParams.offset !== undefined) {
        params = params.set('offset', filterParams.offset.toString());
      }
      if (filterParams.limit !== undefined) {
        params = params.set('limit', filterParams.limit.toString());
      }
      if (filterParams.role !== undefined) {
        params = params.set('role', filterParams.role);
      }
      if (filterParams.grade_level) {
        params = params.set('grade_level', filterParams.grade_level);
      }
    }

    return this.http
      .get<UserResponse[]>(`${this.baseUrl}/`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Récupère un utilisateur par son identifiant unique.
   */
  getById(id: number): Observable<UserResponse> {
    return this.http
      .get<UserResponse>(`${this.baseUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Raccourci pour récupérer spécifiquement les profils enfants (CHILD).
   */
  getChildren(offset = 0, limit = 20, gradeLevel?: string): Observable<UserResponse[]> {
    return this.getAll({
      offset,
      limit,
      role: UserRole.CHILD,
      grade_level: gradeLevel,
    });
  }

  /**
   * Récupère uniquement les enfants rattachés au parent/enseignant connecté (/my-children).
   */
  getMyChildren(gradeLevel?: string): Observable<UserResponse[]> {
    let params = new HttpParams();
    if (gradeLevel) {
      params = params.set('grade_level', gradeLevel);
    }
    return this.http
      .get<UserResponse[]>(`${this.baseUrl}/my-children`, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Crée un profil enfant rattaché au compte connecté (/children).
   */
  createChild(dto: UserCreateDto): Observable<UserResponse> {
    return this.http
      .post<UserResponse>(`${this.baseUrl}/children`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Met à jour un profil enfant rattaché (/children/{child_id}).
   */
  updateChild(childId: number, dto: Partial<UserCreateDto>): Observable<UserResponse> {
    return this.http
      .patch<UserResponse>(`${this.baseUrl}/children/${childId}`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Enregistre un nouvel utilisateur ou profil enfant.
   */
  createChildProfile(dto: UserCreateDto): Observable<UserResponse> {
    return this.http
      .post<UserResponse>(`${this.baseUrl}/`, dto)
      .pipe(catchError(this.handleError));
  }

  create(dto: UserCreateDto): Observable<UserResponse> {
    return this.createChildProfile(dto);
  }

  /**
   * Met à jour partiellement un profil utilisateur (PATCH).
   */
  update(id: number, dto: UserUpdateDto): Observable<UserResponse> {
    return this.http
      .patch<UserResponse>(`${this.baseUrl}/${id}`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Supprime un utilisateur de la base de données.
   */
  delete(id: number): Observable<void> {
    return this.http
      .delete<void>(`${this.baseUrl}/${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Gestionnaire d'erreurs standardisé pour l'API.
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'Une erreur inattendue est survenue.';

    if (error.error instanceof ErrorEvent) {
      // Erreur côté client ou réseau
      errorMessage = `Erreur réseau : ${error.error.message}`;
    } else {
      // Erreur renvoyée par le backend FastAPI
      if (error.status === 0) {
        errorMessage = 'Impossible de joindre le serveur. Vérifie que le backend et la base de données sont démarrés.';
      } else if (error.error && typeof error.error.detail === 'string') {
        errorMessage = error.error.detail;
      } else if (Array.isArray(error.error?.detail)) {
        errorMessage = error.error.detail
          .map((issue: { msg?: string }) => issue.msg)
          .filter((message: string | undefined): message is string => Boolean(message))
          .join(' ');
      } else if (error.status === 404) {
        errorMessage = 'Utilisateur introuvable.';
      } else if (error.status === 400) {
        errorMessage = 'Requête invalide (conflit de données).';
      } else if (error.status >= 500) {
        errorMessage = 'Erreur interne du serveur backend.';
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}
