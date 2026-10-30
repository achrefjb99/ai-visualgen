import { TestBed } from '@angular/core/testing';
import { ActivatedRouteSnapshot, Router, RouterStateSnapshot, UrlTree } from '@angular/router';
import { childRequiredGuard } from './child-required.guard';
import { ChildSessionService } from '../services/child-session.service';
import { signal } from '@angular/core';
import { UserPublic, UserRole } from '../models/auth.model';

describe('childRequiredGuard', () => {
  let mockChildSessionService: {
    activeChild: ReturnType<typeof signal<UserPublic | null>>;
    hasActiveChild: () => boolean;
  };
  let router: Router;

  beforeEach(() => {
    const childSignal = signal<UserPublic | null>(null);
    mockChildSessionService = {
      activeChild: childSignal,
      hasActiveChild: () => !!childSignal(),
    };

    TestBed.configureTestingModule({
      providers: [
        { provide: ChildSessionService, useValue: mockChildSessionService },
      ],
    });

    router = TestBed.inject(Router);
  });

  it('devrait autoriser la navigation si un enfant est actif', () => {
    mockChildSessionService.activeChild.set({
      id: 1,
      username: 'Lina',
      role: UserRole.CHILD,
      age: 7,
      created_at: new Date().toISOString(),
    });

    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/quiz' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => childRequiredGuard(route, state));
    expect(result).toBe(true);
  });

  it('devrait rediriger vers /parent-dashboard si aucun enfant n’est sélectionné', () => {
    mockChildSessionService.activeChild.set(null);

    const route = {} as ActivatedRouteSnapshot;
    const state = { url: '/tutor' } as RouterStateSnapshot;

    const result = TestBed.runInInjectionContext(() => childRequiredGuard(route, state));
    expect(result instanceof UrlTree).toBe(true);
    const tree = result as UrlTree;
    expect(tree.toString()).toContain('/parent-dashboard?returnUrl=%2Ftutor');
  });
});
