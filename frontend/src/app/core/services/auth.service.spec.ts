import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { AuthService, AUTH_TOKEN_KEY } from './auth.service';
import { LoginRequest, TokenResponse, UserPublic, UserRole } from '../models/auth.model';
import { environment } from '../../../environments/environment';

describe('AuthService', () => {
  let service: AuthService;
  let httpMock: HttpTestingController;

  const mockUser: UserPublic = {
    id: 1,
    username: 'prof_dupont',
    email: 'prof@test.com',
    role: UserRole.TEACHER,
    created_at: new Date().toISOString(),
  };

  const mockTokenResponse: TokenResponse = {
    access_token: 'fake-jwt-token',
    token_type: 'bearer',
    user: mockUser,
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [
        AuthService,
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([{ path: 'login', component: class DummyComponent {} }]),
      ],
    });
    service = TestBed.inject(AuthService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
  });

  it('devrait être instancié avec un état non authentifié par défaut', () => {
    expect(service).toBeTruthy();
    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
  });

  it('devrait authentifier l’utilisateur et stocker le token dans localStorage', () => {
    const credentials: LoginRequest = { username: 'prof_dupont', password: 'password123' };

    service.login(credentials).subscribe((res) => {
      expect(res).toEqual(mockTokenResponse);
      expect(service.currentUser()).toEqual(mockUser);
      expect(service.isAuthenticated()).toBe(true);
      expect(service.getToken()).toBe('fake-jwt-token');
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('fake-jwt-token');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/login`);
    expect(req.request.method).toBe('POST');
    req.flush(mockTokenResponse);
  });

  it('devrait supprimer le token et réinitialiser l’utilisateur lors du logout', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'fake-jwt-token');
    service.currentUser.set(mockUser);

    service.logout();

    expect(service.getToken()).toBeNull();
    expect(service.currentUser()).toBeNull();
    expect(service.isAuthenticated()).toBe(false);
  });

  it('devrait restaurer la session via checkSession si un token existe', () => {
    localStorage.setItem(AUTH_TOKEN_KEY, 'stored-token');

    service.checkSession().subscribe((user) => {
      expect(user).toEqual(mockUser);
      expect(service.currentUser()).toEqual(mockUser);
      expect(service.isAuthenticated()).toBe(true);
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/me`);
    expect(req.request.method).toBe('GET');
    req.flush(mockUser);
  });

  it('devrait inscrire un utilisateur et stocker le token dans localStorage', () => {
    const registerDto = {
      username: 'maman_sophie',
      email: 'sophie@test.com',
      password: 'password123',
      role: UserRole.PARENT,
    };

    service.register(registerDto).subscribe((res) => {
      expect(res).toEqual(mockTokenResponse);
      expect(service.currentUser()).toEqual(mockUser);
      expect(service.isAuthenticated()).toBe(true);
      expect(service.getToken()).toBe('fake-jwt-token');
      expect(localStorage.getItem(AUTH_TOKEN_KEY)).toBe('fake-jwt-token');
    });

    const req = httpMock.expectOne(`${environment.apiUrl}/auth/register`);
    expect(req.request.method).toBe('POST');
    req.flush(mockTokenResponse);
  });
});
