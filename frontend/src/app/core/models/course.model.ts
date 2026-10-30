/**
 * Modèles et DTOs pour les cours et les chapitres d'apprentissage (Topics).
 * Aligné avec l'API FastAPI EduGenius AI.
 */

import { UserResponse } from './user.model';

/**
 * Schéma de réponse d'un chapitre pédagogique (Topic).
 */
export interface TopicResponse {
  id: number;
  course_id: number;
  name: string;
  summary_kid: string;
  created_at: string;
  course?: CourseResponse | null;
}

/**
 * DTO de création d'un chapitre rattaché à un cours.
 */
export interface TopicCreateDto {
  course_id: number;
  name: string;
  summary_kid: string;
}

/**
 * DTO de mise à jour d'un chapitre.
 */
export interface TopicUpdateDto {
  course_id?: number;
  name?: string;
  summary_kid?: string;
}

/**
 * Schéma de réponse d'un cours pédagogique.
 */
export interface CourseResponse {
  id: number;
  title: string;
  description?: string | null;
  subject: string;
  grade_level: string;
  teacher_id?: number | null;
  created_at: string;
  teacher?: UserResponse | null;
  topics?: TopicResponse[];
}

/**
 * DTO de création d'un cours.
 */
export interface CourseCreateDto {
  title: string;
  description?: string | null;
  subject: string;
  grade_level: string;
  teacher_id?: number | null;
}

/**
 * DTO de mise à jour d'un cours.
 */
export interface CourseUpdateDto {
  title?: string;
  description?: string | null;
  subject?: string;
  grade_level?: string;
  teacher_id?: number | null;
}

/**
 * Paramètres de filtrage et pagination pour la liste des cours.
 */
export interface CourseFilterParams {
  offset?: number;
  limit?: number;
  subject?: string;
  grade_level?: string;
  teacher_id?: number;
}
