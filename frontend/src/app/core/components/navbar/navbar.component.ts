import { CommonModule } from '@angular/common';
import { Component, computed, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { UserRole } from '../../models/auth.model';
import { AuthService } from '../../services/auth.service';
import { ChildSessionService } from '../../services/child-session.service';

interface RoleBadge {
  label: string;
  emoji: string;
  classes: string;
}

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navbar.component.html',
})
export class NavbarComponent {
  readonly authService = inject(AuthService);
  readonly childSessionService = inject(ChildSessionService);
  private readonly router = inject(Router);

  readonly isMobileMenuOpen = signal<boolean>(false);
  readonly showLogoutModal = signal<boolean>(false);

  // Signals réactifs de session
  readonly currentUser = this.authService.currentUser;
  readonly isAuthenticated = this.authService.isAuthenticated;

  readonly activeChild = this.childSessionService.activeChild;
  readonly hasActiveChild = this.childSessionService.hasActiveChild;
  readonly activeGrade = this.childSessionService.activeGrade;
  readonly activeTheme = this.childSessionService.activeTheme;

  // Calcul des privilèges d'accès
  readonly isTeacher = computed<boolean>(() => {
    const role = this.currentUser()?.role;
    return role === UserRole.TEACHER || role === UserRole.ADMIN;
  });

  readonly isParent = computed<boolean>(() => {
    const role = this.currentUser()?.role;
    return role === UserRole.PARENT || role === UserRole.ADMIN;
  });

  readonly isChild = computed<boolean>(() => {
    return this.currentUser()?.role === UserRole.CHILD;
  });

  readonly showStudentLinks = computed<boolean>(() => {
    // Les onglets élèves (Flashcards, Buddy Tuteur, Quiz) ne s'affichent pas pour l'enseignant
    if (this.isTeacher()) {
      return false;
    }
    return this.hasActiveChild() || this.isChild();
  });

  readonly homeRoute = computed<string>(() => {
    if (this.hasActiveChild()) {
      const child = this.activeChild();
      return child ? `/home/${child.id}` : '/parent-dashboard';
    }
    if (this.currentUser()?.role === UserRole.TEACHER) {
      return '/teacher-dashboard';
    }
    return '/parent-dashboard';
  });

  readonly roleBadge = computed<RoleBadge>(() => {
    const user = this.currentUser();
    if (!user) {
      return { label: 'Invité', emoji: '👋', classes: 'bg-slate-100 text-slate-700' };
    }

    switch (user.role) {
      case UserRole.CHILD:
        return {
          label: 'Aventurier',
          emoji: '🎒',
          classes: 'bg-emerald-100 text-emerald-800 border-emerald-200',
        };
      case UserRole.PARENT:
        return {
          label: 'Parent',
          emoji: '👨‍👩‍👧',
          classes: 'bg-amber-100 text-amber-800 border-amber-200',
        };
      case UserRole.TEACHER:
        return {
          label: 'Enseignant',
          emoji: '🧑‍🏫',
          classes: 'bg-sky-100 text-sky-800 border-sky-200',
        };
      case UserRole.ADMIN:
        return {
          label: 'Admin',
          emoji: '🛡️',
          classes: 'bg-purple-100 text-purple-800 border-purple-200',
        };
      default:
        return {
          label: 'Membre',
          emoji: '⭐',
          classes: 'bg-slate-100 text-slate-800 border-slate-200',
        };
    }
  });

  toggleMobileMenu(): void {
    this.isMobileMenuOpen.update((v) => !v);
  }

  closeMobileMenu(): void {
    this.isMobileMenuOpen.set(false);
  }

  exitChildMode(): void {
    this.closeMobileMenu();
    this.childSessionService.clearActiveChild();
    this.router.navigate(['/parent-dashboard']);
  }

  promptLogout(): void {
    this.showLogoutModal.set(true);
  }

  cancelLogout(): void {
    this.showLogoutModal.set(false);
  }

  confirmLogout(): void {
    this.showLogoutModal.set(false);
    this.closeMobileMenu();
    this.authService.logout();
  }
}
