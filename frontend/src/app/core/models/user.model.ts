/**
 * Modèles et DTOs pour la gestion des utilisateurs et des profils enfants.
 * Aligné avec l'API FastAPI EduGenius AI.
 */

import { CourseResponse } from './course.model';

export enum UserRole {
  CHILD = 'CHILD',
  PARENT = 'PARENT',
  TEACHER = 'TEACHER',
  ADMIN = 'ADMIN',
}

/**
 * Schéma de réponse d'un utilisateur renvoyé par l'API (mot de passe exclu).
 */
export interface UserResponse {
  id: number;
  username: string;
  email?: string | null;
  role: UserRole;
  age?: number | null;
  grade_level?: string | null;
  favorite_theme?: string | null;
  parent_id?: number | null;
  created_at: string;
  courses?: CourseResponse[];
}

/**
 * DTO pour l'enregistrement ou la création d'un utilisateur (mot de passe en clair).
 */
export interface UserCreateDto {
  username: string;
  email?: string | null;
  password?: string;
  role?: UserRole;
  age?: number | null;
  grade_level?: string | null;
  favorite_theme?: string | null;
  parent_id?: number | null;
}

/**
 * DTO pour la mise à jour partielle (PATCH) d'un profil utilisateur.
 */
export interface UserUpdateDto {
  username?: string;
  email?: string;
  password?: string;
  role?: UserRole;
  age?: number | null;
  grade_level?: string | null;
  favorite_theme?: string | null;
}

/**
 * Paramètres de filtrage et pagination pour la liste des utilisateurs.
 */
export interface UserFilterParams {
  offset?: number;
  limit?: number;
  role?: UserRole;
  grade_level?: string;
}
