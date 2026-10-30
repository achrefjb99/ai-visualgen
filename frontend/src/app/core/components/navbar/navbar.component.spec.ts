import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { NavbarComponent } from './navbar.component';
import { AuthService } from '../../services/auth.service';
import { ChildSessionService } from '../../services/child-session.service';
import { UserRole } from '../../models/auth.model';

describe('NavbarComponent', () => {
  let component: NavbarComponent;
  let authService: AuthService;
  let childSessionService: ChildSessionService;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [NavbarComponent],
      providers: [
        provideRouter([
          { path: 'parent-dashboard', children: [] },
          { path: 'teacher-dashboard', children: [] },
          { path: 'home/:id', children: [] },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(NavbarComponent);
    component = fixture.componentInstance;
    authService = TestBed.inject(AuthService);
    childSessionService = TestBed.inject(ChildSessionService);
    router = TestBed.inject(Router);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('devrait instancier la navbar', () => {
    expect(component).toBeTruthy();
    expect(component.isAuthenticated()).toBe(false);
  });

  it('devrait calculer le badge et les privilèges d’un enseignant', () => {
    authService.currentUser.set({
      id: 1,
      username: 'Mme Martin',
      role: UserRole.TEACHER,
      created_at: new Date().toISOString(),
    });

    expect(component.isAuthenticated()).toBe(true);
    expect(component.isTeacher()).toBe(true);
    expect(component.isParent()).toBe(false);
    expect(component.roleBadge().label).toBe('Enseignant');
    expect(component.roleBadge().emoji).toBe('🧑‍🏫');
    expect(component.homeRoute()).toBe('/teacher-dashboard');
    expect(component.showStudentLinks()).toBe(false);
  });

  it('devrait calculer les privilèges d’un parent', () => {
    authService.currentUser.set({
      id: 2,
      username: 'M. Dupont',
      role: UserRole.PARENT,
      created_at: new Date().toISOString(),
    });

    expect(component.isAuthenticated()).toBe(true);
    expect(component.isTeacher()).toBe(false);
    expect(component.isParent()).toBe(true);
    expect(component.homeRoute()).toBe('/parent-dashboard');
  });

  it('devrait gérer la session enfant et quitter le mode enfant sans recharger', () => {
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    const clearSpy = vi.spyOn(childSessionService, 'clearActiveChild');

    childSessionService.selectChild({
      id: 42,
      username: 'Lina',
      role: UserRole.CHILD,
      age: 7,
      grade_level: '2ème primaire (CE1)',
      favorite_theme: 'Magie',
      created_at: new Date().toISOString(),
    });

    expect(component.hasActiveChild()).toBe(true);
    expect(component.activeChild()?.username).toBe('Lina');
    expect(component.homeRoute()).toBe('/home/42');

    component.exitChildMode();

    expect(clearSpy).toHaveBeenCalled();
    expect(navigateSpy).toHaveBeenCalledWith(['/parent-dashboard']);
  });

  it('devrait ouvrir et fermer le menu mobile', () => {
    expect(component.isMobileMenuOpen()).toBe(false);
    component.toggleMobileMenu();
    expect(component.isMobileMenuOpen()).toBe(true);
    component.closeMobileMenu();
    expect(component.isMobileMenuOpen()).toBe(false);
  });
});
