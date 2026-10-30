/**
 * Service Angular de gestion des cours et des chapitres pédagogiques (Topics).
 * Utilise l'injection moderne Angular 18 et la gestion réactive RxJS.
 */

import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { environment } from '../../../environments/environment';
import {
  CourseCreateDto,
  CourseFilterParams,
  CourseResponse,
  CourseUpdateDto,
  TopicCreateDto,
  TopicResponse,
  TopicUpdateDto,
} from '../models/course.model';

@Injectable({
  providedIn: 'root',
})
export class CourseService {
  private readonly http = inject(HttpClient);
  private readonly api = environment.apiUrl.replace(/\/+$/, '');
  private readonly coursesUrl = `${this.api}/courses/`;
  private readonly topicsUrl = `${this.api}/topics/`;

  // ===========================================================================
  // OPÉRATIONS COURS (COURSES)
  // ===========================================================================

  /**
   * Récupère la liste paginée des cours avec filtres par matière, niveau ou enseignant.
   */
  getAll(filterParams?: CourseFilterParams): Observable<CourseResponse[]> {
    let params = new HttpParams();

    if (filterParams) {
      if (filterParams.offset !== undefined) {
        params = params.set('offset', filterParams.offset.toString());
      }
      if (filterParams.limit !== undefined) {
        params = params.set('limit', filterParams.limit.toString());
      }
      if (filterParams.subject) {
        params = params.set('subject', filterParams.subject);
      }
      if (filterParams.grade_level) {
        params = params.set('grade_level', filterParams.grade_level);
      }
      if (filterParams.teacher_id !== undefined) {
        params = params.set('teacher_id', filterParams.teacher_id.toString());
      }
    }

    return this.http
      .get<CourseResponse[]>(this.coursesUrl, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Récupère les détails d'un cours (avec ses chapitres et son enseignant).
   */
  getById(id: number): Observable<CourseResponse> {
    return this.http
      .get<CourseResponse>(`${this.coursesUrl}${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Crée un nouveau cours pédagogique.
   */
  create(dto: CourseCreateDto): Observable<CourseResponse> {
    return this.http
      .post<CourseResponse>(this.coursesUrl, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Met à jour partiellement un cours (PATCH).
   */
  update(id: number, dto: CourseUpdateDto): Observable<CourseResponse> {
    return this.http
      .patch<CourseResponse>(`${this.coursesUrl}${id}`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Supprime un cours (entraîne la suppression en cascade de ses chapitres).
   */
  delete(id: number): Observable<void> {
    return this.http
      .delete<void>(`${this.coursesUrl}${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Récupère spécifiquement la liste paginée des chapitres d'un cours donné.
   */
  getTopicsByCourse(courseId: number, offset = 0, limit = 20): Observable<TopicResponse[]> {
    const params = new HttpParams()
      .set('offset', offset.toString())
      .set('limit', limit.toString());

    return this.http
      .get<TopicResponse[]>(`${this.api}/courses/${courseId}/topics`, { params })
      .pipe(catchError(this.handleError));
  }

  // ===========================================================================
  // OPÉRATIONS CHAPITRES (TOPICS)
  // ===========================================================================

  /**
   * Récupère la liste des chapitres avec filtre optionnel par cours.
   */
  getAllTopics(courseId?: number, offset = 0, limit = 20): Observable<TopicResponse[]> {
    let params = new HttpParams()
      .set('offset', offset.toString())
      .set('limit', limit.toString());

    if (courseId !== undefined) {
      params = params.set('course_id', courseId.toString());
    }

    return this.http
      .get<TopicResponse[]>(this.topicsUrl, { params })
      .pipe(catchError(this.handleError));
  }

  /**
   * Récupère un chapitre par son identifiant.
   */
  getTopicById(id: number): Observable<TopicResponse> {
    return this.http
      .get<TopicResponse>(`${this.topicsUrl}${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Crée un nouveau chapitre adapté aux enfants.
   */
  createTopic(dto: TopicCreateDto): Observable<TopicResponse> {
    return this.http
      .post<TopicResponse>(this.topicsUrl, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Met à jour un chapitre existant.
   */
  updateTopic(id: number, dto: TopicUpdateDto): Observable<TopicResponse> {
    return this.http
      .patch<TopicResponse>(`${this.topicsUrl}${id}`, dto)
      .pipe(catchError(this.handleError));
  }

  /**
   * Supprime un chapitre.
   */
  deleteTopic(id: number): Observable<void> {
    return this.http
      .delete<void>(`${this.topicsUrl}${id}`)
      .pipe(catchError(this.handleError));
  }

  /**
   * Gestionnaire d'erreurs HTTP standardisé.
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'Une erreur est survenue lors de la communication avec le serveur.';

    if (error.error instanceof ErrorEvent) {
      errorMessage = `Erreur réseau : ${error.error.message}`;
    } else {
      if (error.error && typeof error.error.detail === 'string') {
        errorMessage = error.error.detail;
      } else if (error.status === 404) {
        errorMessage = 'La ressource demandée (cours ou chapitre) est introuvable.';
      } else if (error.status === 400) {
        errorMessage = 'Données invalides fournies pour le cours ou chapitre.';
      } else if (error.status >= 500) {
        errorMessage = 'Erreur interne du serveur backend.';
      }
    }

    return throwError(() => new Error(errorMessage));
  }
}
