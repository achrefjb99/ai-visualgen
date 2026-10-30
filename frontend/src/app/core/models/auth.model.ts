/**
 * Modèles et interfaces TypeScript pour le système d'authentification JWT (Module 1).
 * Aligné avec l'API FastAPI EduGenius AI (/api/v1/auth).
 */

import { UserRole } from './user.model';
export { UserRole };

/**
 * Données d'identification pour la requête de connexion.
 */
export interface LoginRequest {
  username: string;
  password: string;
}

/**
 * Données d'inscription publique (Parent ou Enseignant).
 */
export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role: UserRole;
}

/**
 * Informations publiques du profil utilisateur retournées par l'API (/auth/me).
 */
export interface UserPublic {
  id: number;
  username: string;
  email?: string | null;
  role: UserRole;
  age?: number | null;
  grade_level?: string | null;
  favorite_theme?: string | null;
  parent_id?: number | null;
  created_at: string;
}

/**
 * Réponse renvoyée par le serveur lors d'une authentification réussie (/auth/token ou /auth/login).
 */
export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserPublic;
}
