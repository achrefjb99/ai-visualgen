import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting, HttpTestingController } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { ParentDashboardComponent } from './parent-dashboard.component';
import { UserService } from '../../../core/services/user.service';
import { AuthService } from '../../../core/services/auth.service';
import { ChildSessionService } from '../../../core/services/child-session.service';
import { UserCreateDto, UserResponse, UserRole } from '../../../core/models/user.model';
import { of } from 'rxjs';

describe('ParentDashboardComponent', () => {
  let component: ParentDashboardComponent;
  let userService: UserService;
  let authService: AuthService;
  let childSessionService: ChildSessionService;
  let router: Router;

  const mockParent = {
    id: 10,
    username: 'Parent Jean',
    role: UserRole.PARENT,
    created_at: new Date().toISOString(),
  };

  const mockChildren: UserResponse[] = [
    {
      id: 101,
      username: 'Lina',
      role: UserRole.CHILD,
      age: 7,
      grade_level: '2ème primaire (CE1)',
      favorite_theme: 'Magie',
      parent_id: 10,
      created_at: new Date().toISOString(),
    },
    {
      id: 102,
      username: 'Yassine',
      role: UserRole.CHILD,
      age: 10,
      grade_level: '4ème primaire (CM1)',
      favorite_theme: 'Dinosaures',
      parent_id: 10,
      created_at: new Date().toISOString(),
    },
  ];

  beforeEach(async () => {
    localStorage.clear();
    await TestBed.configureTestingModule({
      imports: [ParentDashboardComponent],
      providers: [
        provideRouter([
          { path: 'home/:childId', children: [] },
          { path: 'progress', children: [] },
        ]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    userService = TestBed.inject(UserService);
    authService = TestBed.inject(AuthService);
    childSessionService = TestBed.inject(ChildSessionService);
    router = TestBed.inject(Router);

    authService.currentUser.set(mockParent);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('devrait instancier le tableau de bord et charger les enfants', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of(mockChildren));

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component).toBeTruthy();
    expect(component.parentName()).toBe('Parent Jean');
    expect(component.children().length).toBe(2);
    expect(component.hasChildren()).toBe(true);
  });

  it('devrait ouvrir et fermer la modale d’ajout d’enfant', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of(mockChildren));
    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.isAddModalOpen()).toBe(false);
    component.openAddModal();
    expect(component.isAddModalOpen()).toBe(true);
    expect(component.childForm.value.username).toBe('');

    component.closeAddModal();
    expect(component.isAddModalOpen()).toBe(false);
  });

  it('devrait sélectionner un thème dans le formulaire', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of([]));
    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openAddModal();
    component.selectTheme('Espace');
    expect(component.childForm.value.favorite_theme).toBe('Espace');
  });

  it('devrait ajouter un enfant via le formulaire', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of([]));
    const newChild: UserResponse = {
      id: 103,
      username: 'Léo',
      role: UserRole.CHILD,
      age: 8,
      grade_level: '3ème primaire (CE2)',
      favorite_theme: 'Animaux',
      parent_id: 10,
      created_at: new Date().toISOString(),
    };
    vi.spyOn(userService, 'createChild').mockReturnValue(of(newChild));

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openAddModal();
    component.childForm.patchValue({
      username: 'Léo',
      age: 8,
      grade_level: '3ème primaire (CE2)',
      favorite_theme: 'Animaux',
    });

    component.submitAddChild();

    expect(component.children().length).toBe(1);
    expect(component.children()[0].username).toBe('Léo');
    expect(component.isAddModalOpen()).toBe(false);
    expect(component.feedbackMessage()?.type).toBe('success');
  });

  it('devrait lancer l’aventure et configurer l’enfant actif', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of(mockChildren));
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);
    const selectChildSpy = vi.spyOn(childSessionService, 'selectChild');

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.launchAdventure(mockChildren[0]);

    expect(selectChildSpy).toHaveBeenCalledWith(mockChildren[0]);
    expect(navigateSpy).toHaveBeenCalledWith(['/home', mockChildren[0].id]);
  });

  it('devrait ouvrir et fermer la modale de suppression et supprimer l’enfant', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of([...mockChildren]));
    vi.spyOn(userService, 'delete').mockReturnValue(of(void 0));

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openDeleteModal(mockChildren[0]);
    expect(component.childToDelete()?.id).toBe(101);

    component.confirmDelete();
    expect(component.children().length).toBe(1);
    expect(component.children()[0].id).toBe(102);
    expect(component.childToDelete()).toBeNull();
  });

  it('devrait ouvrir la modale d’aperçu des progrès et naviguer vers le rapport complet', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of(mockChildren));
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true);

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openProgressPreview(mockChildren[1]);
    expect(component.previewChildProgress()?.id).toBe(102);

    component.goToFullProgress(mockChildren[1]);
    expect(component.previewChildProgress()).toBeNull();
    expect(navigateSpy).toHaveBeenCalledWith(['/progress'], { queryParams: { child: 102 } });
  });

  it('devrait ouvrir la modale de modification pré-remplie avec les données de l’enfant', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of(mockChildren));
    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openEditModal(mockChildren[0]);

    expect(component.childToEdit()?.id).toBe(101);
    expect(component.editChildForm.value.username).toBe('Lina');
    expect(component.editChildForm.value.age).toBe(7);
    expect(component.editChildForm.value.grade_level).toBe('2ème primaire (CE1)');
    expect(component.editChildForm.value.favorite_theme).toBe('Magie');

    component.selectEditTheme('Espace');
    expect(component.editChildForm.value.favorite_theme).toBe('Espace');

    component.closeEditModal();
    expect(component.childToEdit()).toBeNull();
  });

  it('devrait modifier un profil enfant et mettre à jour la liste et l’enfant actif', () => {
    vi.spyOn(userService, 'getMyChildren').mockReturnValue(of([...mockChildren]));
    const selectChildSpy = vi.spyOn(childSessionService, 'selectChild');

    // Simuler que l'enfant 101 est actuellement actif
    childSessionService.activeChild.set(mockChildren[0]);

    const updatedChild: UserResponse = {
      ...mockChildren[0],
      age: 8,
      grade_level: '3ème primaire (CE2)',
      favorite_theme: 'Espace',
    };
    vi.spyOn(userService, 'updateChild').mockReturnValue(of(updatedChild));

    const fixture = TestBed.createComponent(ParentDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.openEditModal(mockChildren[0]);
    component.editChildForm.patchValue({
      age: 8,
      grade_level: '3ème primaire (CE2)',
      favorite_theme: 'Espace',
    });

    component.submitEditChild();

    expect(component.childToEdit()).toBeNull();
    expect(component.children()[0].age).toBe(8);
    expect(component.children()[0].favorite_theme).toBe('Espace');
    expect(selectChildSpy).toHaveBeenCalledWith(updatedChild);
    expect(component.feedbackMessage()?.type).toBe('success');
  });
});
