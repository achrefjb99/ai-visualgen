import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { roleGuard } from './role.guard';
import { AuthService } from '../services/auth.service';
import { signal } from '@angular/core';
import { UserPublic, UserRole } from '../models/auth.model';

describe('roleGuard', () => {
  let mockAuthService: {
    currentUser: ReturnType<typeof signal<UserPublic | null>>;
    isAuthenticated: () => boolean;
  };
  let router: Router;

  beforeEach(() => {
    const userSignal = signal<UserPublic | null>(null);
    mockAuthService = {
      currentUser: userSignal,
      isAuthenticated: () => !!userSignal(),
    };

    TestBed.configureTestingModule({
      providers: [{ provide: AuthService, useValue: mockAuthService }],
    });

    router = TestBed.inject(Router);
  });

  it('devrait autoriser l’accès si le rôle de l’utilisateur figure dans data.roles', () => {
    mockAuthService.currentUser.set({
      id: 1,
      username: 'maman',
      role: UserRole.PARENT,
      created_at: new Date().toISOString(),
    });

    const route = {
      data: { roles: [UserRole.PARENT, UserRole.ADMIN] },
    } as unknown as ActivatedRouteSnapshot;
    const state = { url: '/parent-dashboard' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => roleGuard(route, state));
    expect(result).toBe(true);
  });

  it('devrait rediriger un enseignant vers /teacher-dashboard s’il tente d’accéder à une route parent', () => {
    mockAuthService.currentUser.set({
      id: 2,
      username: 'prof',
      role: UserRole.TEACHER,
      created_at: new Date().toISOString(),
    });

    const route = {
      data: { roles: [UserRole.PARENT, UserRole.ADMIN] },
    } as unknown as ActivatedRouteSnapshot;
    const state = { url: '/parent-dashboard' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => roleGuard(route, state));
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toBe('/teacher-dashboard');
  });

  it('devrait rediriger vers /login si non authentifié', () => {
    mockAuthService.currentUser.set(null);

    const route = {
      data: { roles: [UserRole.PARENT] },
    } as unknown as ActivatedRouteSnapshot;
    const state = { url: '/parent-dashboard' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => roleGuard(route, state));
    expect(result instanceof UrlTree).toBe(true);
    expect((result as UrlTree).toString()).toContain('/login');
  });
});
