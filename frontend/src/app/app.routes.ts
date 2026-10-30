import { inject } from '@angular/core';
import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { childRequiredGuard } from './core/guards/child-required.guard';
import { roleGuard } from './core/guards/role.guard';
import { AuthService } from './core/services/auth.service';
import { UserRole } from './core/models/auth.model';
import { LoginComponent } from './features/auth/login/login.component';

export const routes: Routes = [
  // 1. Redirection par défaut selon le rôle et l'état d'authentification
  {
    path: '',
    pathMatch: 'full',
    redirectTo: () => {
      const auth = inject(AuthService);
      if (!auth.isAuthenticated()) return 'login';
      return auth.currentUser()?.role === UserRole.TEACHER
        ? 'teacher-dashboard'
        : 'parent-dashboard';
    },
  },

  // 2. Authentification publique
  {
    path: 'login',
    component: LoginComponent,
  },
  {
    path: 'register',
    loadComponent: () =>
      import('./features/auth/register/register.component').then(
        (m) => m.RegisterComponent
      ),
  },

  // 3. Espace Parent / Supervision (Accessible PARENT & ADMIN)
  {
    path: 'parent-dashboard',
    canActivate: [authGuard, roleGuard],
    data: { roles: [UserRole.PARENT, UserRole.ADMIN] },
    loadComponent: () =>
      import('./features/parent/parent-dashboard/parent-dashboard.component').then(
        (m) => m.ParentDashboardComponent
      ),
  },
  {
    path: 'profile-manager',
    redirectTo: 'parent-dashboard',
    pathMatch: 'full',
  },
  {
    path: 'children',
    redirectTo: 'parent-dashboard',
    pathMatch: 'full',
  },

  // 4. Espace Enseignant & Gestion des Cours (Accessible TEACHER & ADMIN)
  {
    path: 'teacher-dashboard',
    canActivate: [authGuard, roleGuard],
    data: { roles: [UserRole.TEACHER, UserRole.ADMIN] },
    loadComponent: () =>
      import('./features/teacher/teacher-dashboard/teacher-dashboard.component').then(
        (m) => m.TeacherDashboardComponent
      ),
  },

  // 5. Espaces d'apprentissage de l'enfant (protégés par authGuard et childRequiredGuard)
  {
    path: 'home/:id',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/home/child-home/child-home.component').then(
        (m) => m.ChildHomeComponent
      ),
  },
  {
    path: 'module2',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/module2/lesson-flashcards/lesson-flashcards.component').then(
        (m) => m.LessonFlashcardsComponent
      ),
  },
  {
    path: 'tutor',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/learning/learning.component').then((m) => m.LearningComponent),
    data: { mode: 'tutor' },
  },
  {
    path: 'quiz',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/learning/learning.component').then((m) => m.LearningComponent),
    data: { mode: 'quiz' },
  },
  {
    path: 'visuals',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/learning/learning.component').then((m) => m.LearningComponent),
    data: { mode: 'visual' },
  },
  {
    path: 'visualgen',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/visualgen/visualgen/visualgen.component').then(
        (m) => m.VisualGenComponent
      ),
  },
  {
    path: 'learning',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/learning/learning.component').then((m) => m.LearningComponent),
    data: { mode: 'learning' },
  },
  {
    path: 'progress',
    canActivate: [authGuard, childRequiredGuard],
    loadComponent: () =>
      import('./features/learning/learning.component').then((m) => m.LearningComponent),
    data: { mode: 'progress' },
  },

  // 6. Fallback wildcard
  {
    path: '**',
    redirectTo: () => {
      const auth = inject(AuthService);
      if (!auth.isAuthenticated()) return 'login';
      return auth.currentUser()?.role === UserRole.TEACHER
        ? 'teacher-dashboard'
        : 'parent-dashboard';
    },
  },
];
