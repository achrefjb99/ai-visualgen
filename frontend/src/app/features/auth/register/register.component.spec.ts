import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { RegisterComponent } from './register.component';
import { AuthService } from '../../../core/services/auth.service';
import { UserRole } from '../../../core/models/auth.model';
import { of, throwError } from 'rxjs';

describe('RegisterComponent', () => {
  let component: RegisterComponent;
  let authService: AuthService;
  let router: Router;

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [RegisterComponent],
      providers: [
        provideRouter([
          { path: 'parent-dashboard', children: [] },
          { path: 'teacher-dashboard', children: [] },
          { path: 'login', children: [] },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    const fixture = TestBed.createComponent(RegisterComponent);
    component = fixture.componentInstance;
    authService = TestBed.inject(AuthService);
    router = TestBed.inject(Router);
    fixture.detectChanges();
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('devrait initialiser le composant avec le rôle PARENT par défaut', () => {
    expect(component).toBeTruthy();
    expect(component.registerForm.value.role).toBe(UserRole.PARENT);
  });

  it('devrait détecter si les mots de passe ne correspondent pas', () => {
    component.registerForm.patchValue({
      password: 'password123',
      confirmPassword: 'differentpassword',
    });

    expect(component.registerForm.hasError('passwordMismatch')).toBe(true);

    component.registerForm.patchValue({
      confirmPassword: 'password123',
    });

    expect(component.registerForm.hasError('passwordMismatch')).toBe(false);
  });

  it('devrait changer le rôle sélectionné', () => {
    component.selectRole(UserRole.TEACHER);
    expect(component.registerForm.value.role).toBe(UserRole.TEACHER);
  });

  it('devrait basculer l’affichage des mots de passe', () => {
    expect(component.showPassword()).toBe(false);
    component.toggleShowPassword();
    expect(component.showPassword()).toBe(true);

    expect(component.showConfirmPassword()).toBe(false);
    component.toggleShowConfirmPassword();
    expect(component.showConfirmPassword()).toBe(true);
  });

  it('devrait inscrire un parent et rediriger vers /parent-dashboard', () => {
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    vi.spyOn(authService, 'register').mockReturnValue(
      of({
        access_token: 'fake-token',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'maman_sophie',
          email: 'sophie@example.com',
          role: UserRole.PARENT,
          created_at: new Date().toISOString(),
        },
      })
    );

    component.registerForm.patchValue({
      role: UserRole.PARENT,
      username: 'maman_sophie',
      email: 'sophie@example.com',
      password: 'Password123!',
      confirmPassword: 'Password123!',
    });

    component.onSubmit();

    expect(authService.register).toHaveBeenCalledWith({
      username: 'maman_sophie',
      email: 'sophie@example.com',
      password: 'Password123!',
      role: UserRole.PARENT,
    });
    expect(navigateSpy).toHaveBeenCalledWith(['/parent-dashboard']);
    expect(component.isLoading()).toBe(false);
  });

  it('devrait inscrire un enseignant et rediriger vers /teacher-dashboard', () => {
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    vi.spyOn(authService, 'register').mockReturnValue(
      of({
        access_token: 'fake-token',
        token_type: 'bearer',
        user: {
          id: 2,
          username: 'prof_laurent',
          email: 'laurent@ecole.fr',
          role: UserRole.TEACHER,
          created_at: new Date().toISOString(),
        },
      })
    );

    component.registerForm.patchValue({
      role: UserRole.TEACHER,
      username: 'prof_laurent',
      email: 'laurent@ecole.fr',
      password: 'LaurentPassword123!',
      confirmPassword: 'LaurentPassword123!',
    });

    component.onSubmit();

    expect(navigateSpy).toHaveBeenCalledWith(['/teacher-dashboard']);
  });

  it('devrait afficher une erreur retournée par l’API en cas d’échec', () => {
    vi.spyOn(authService, 'register').mockReturnValue(
      throwError(() => ({
        status: 400,
        error: { detail: 'Le nom d’utilisateur est déjà utilisé.' },
      }))
    );

    component.registerForm.patchValue({
      role: UserRole.PARENT,
      username: 'doublon',
      email: 'test@example.com',
      password: 'Password123!',
      confirmPassword: 'Password123!',
    });

    component.onSubmit();

    expect(component.isLoading()).toBe(false);
    expect(component.errorMessage()).toBe('Le nom d’utilisateur est déjà utilisé.');
  });
});
