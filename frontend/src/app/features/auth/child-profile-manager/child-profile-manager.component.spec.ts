import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { UserRole } from '../../../core/models/user.model';
import { UserService } from '../../../core/services/user.service';
import { ChildProfileManagerComponent } from './child-profile-manager.component';

describe('ChildProfileManagerComponent', () => {
  let mockUserService: Partial<UserService>;

  beforeEach(async () => {
    mockUserService = {
      getChildren: () =>
        of([
          {
            id: 1,
            username: 'Léo Test',
            email: 'leo@test.com',
            role: UserRole.CHILD,
            age: 8,
            grade_level: '2ème primaire (CE1)',
            favorite_theme: 'Dinosaures',
            created_at: new Date().toISOString(),
          },
        ]),
      create: (dto) =>
        of({
          id: 2,
          username: dto.username,
          email: dto.email,
          role: UserRole.CHILD,
          age: dto.age,
          grade_level: dto.grade_level,
          favorite_theme: dto.favorite_theme,
          created_at: new Date().toISOString(),
        }),
      delete: () => of(void 0),
    };

    await TestBed.configureTestingModule({
      imports: [ChildProfileManagerComponent],
      providers: [
        { provide: UserService, useValue: mockUserService },
        provideRouter([]),
      ],
    }).compileComponents();
  });

  it('devrait instancier le composant', () => {
    const fixture = TestBed.createComponent(ChildProfileManagerComponent);
    const component = fixture.componentInstance;
    expect(component).toBeTruthy();
  });

  it('devrait charger les profils enfants à l\'initialisation', () => {
    const fixture = TestBed.createComponent(ChildProfileManagerComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    expect(component.children().length).toBe(1);
    expect(component.children()[0].username).toBe('Léo Test');
  });

  it('devrait initialiser le formulaire avec des valeurs par défaut valides', () => {
    const fixture = TestBed.createComponent(ChildProfileManagerComponent);
    const component = fixture.componentInstance;
    expect(component.profileForm.get('favorite_theme')?.value).toBe('Dinosaures');
    expect(component.profileForm.get('age')?.value).toBe(7);
  });
});
