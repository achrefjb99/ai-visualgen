import { TestBed } from '@angular/core/testing';
import { ChildSessionService, ACTIVE_CHILD_STORAGE_KEY } from './child-session.service';
import { UserPublic, UserRole } from '../models/auth.model';

describe('ChildSessionService', () => {
  let service: ChildSessionService;

  const mockChild1: UserPublic = {
    id: 10,
    username: 'Yassine',
    role: UserRole.CHILD,
    age: 10,
    grade_level: 'CM1',
    favorite_theme: 'Dinosaures',
    created_at: new Date().toISOString(),
  };

  const mockChild2: UserPublic = {
    id: 20,
    username: 'Lina',
    role: UserRole.CHILD,
    age: 7,
    grade_level: 'CP',
    favorite_theme: 'Magie',
    created_at: new Date().toISOString(),
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [ChildSessionService],
    });
    service = TestBed.inject(ChildSessionService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('devrait être initialisé sans enfant actif par défaut', () => {
    expect(service.activeChild()).toBeNull();
    expect(service.hasActiveChild()).toBe(false);
    expect(service.activeTheme()).toBe('space');
    expect(service.activeGrade()).toBe('CE2');
  });

  it('devrait sélectionner un enfant et persister son ID dans localStorage', () => {
    service.selectChild(mockChild1);

    expect(service.activeChild()).toEqual(mockChild1);
    expect(service.hasActiveChild()).toBe(true);
    expect(service.activeTheme()).toBe('Dinosaures');
    expect(service.activeGrade()).toBe('CM1');
    expect(localStorage.getItem(ACTIVE_CHILD_STORAGE_KEY)).toBe('10');
  });

  it('devrait réinitialiser la session enfant lors de clearActiveChild', () => {
    service.selectChild(mockChild1);
    expect(service.hasActiveChild()).toBe(true);

    service.clearActiveChild();

    expect(service.activeChild()).toBeNull();
    expect(service.hasActiveChild()).toBe(false);
    expect(localStorage.getItem(ACTIVE_CHILD_STORAGE_KEY)).toBeNull();
  });

  it('devrait restaurer l’enfant actif depuis localStorage si présent dans la liste', () => {
    localStorage.setItem(ACTIVE_CHILD_STORAGE_KEY, '20');

    service.restoreActiveChild([mockChild1, mockChild2]);

    expect(service.activeChild()).toEqual(mockChild2);
    expect(service.hasActiveChild()).toBe(true);
    expect(service.activeTheme()).toBe('Magie');
    expect(service.activeGrade()).toBe('CP');
  });

  it('devrait vider la persistance si l’ID stocké n’existe plus dans la liste', () => {
    localStorage.setItem(ACTIVE_CHILD_STORAGE_KEY, '999');

    service.restoreActiveChild([mockChild1, mockChild2]);

    expect(service.activeChild()).toBeNull();
    expect(service.hasActiveChild()).toBe(false);
    expect(localStorage.getItem(ACTIVE_CHILD_STORAGE_KEY)).toBeNull();
  });
});
