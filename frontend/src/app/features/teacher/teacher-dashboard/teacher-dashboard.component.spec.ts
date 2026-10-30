import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { TeacherDashboardComponent } from './teacher-dashboard.component';
import { CourseService } from '../../../core/services/course.service';
import { Module2Service } from '../../../core/services/module2.service';
import { AuthService } from '../../../core/services/auth.service';
import { CourseResponse } from '../../../core/models/course.model';
import { UserRole } from '../../../core/models/user.model';

describe('TeacherDashboardComponent', () => {
  let component: TeacherDashboardComponent;
  let courseService: CourseService;
  let module2Service: Module2Service;
  let authService: AuthService;

  const mockTeacher = {
    id: 5,
    username: 'Professeur Tournesol',
    role: UserRole.TEACHER,
    created_at: new Date().toISOString(),
  };

  const mockCourses: CourseResponse[] = [
    {
      id: 1,
      title: "Le cycle de l'eau",
      subject: 'Sciences',
      grade_level: 'CE2',
      teacher_id: 5,
      created_at: '2026-10-24T10:00:00Z',
      topics: [
        {
          id: 10,
          course_id: 1,
          name: "L'évaporation et la pluie",
          summary_kid: "L'eau monte au ciel sous forme de vapeur puis retombe en pluie.",
          created_at: '2026-10-24T10:05:00Z',
        },
      ],
    },
    {
      id: 2,
      title: 'Les Gaulois et les Romains',
      subject: 'Histoire',
      grade_level: 'CM1',
      teacher_id: 5,
      created_at: '2026-10-24T11:00:00Z',
      topics: [],
    },
  ];

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TeacherDashboardComponent],
      providers: [
        provideRouter([]),
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    }).compileComponents();

    courseService = TestBed.inject(CourseService);
    module2Service = TestBed.inject(Module2Service);
    authService = TestBed.inject(AuthService);

    // Mock teacher authentication
    authService.currentUser.set(mockTeacher);

    // Mock CourseService.getAll
    vi.spyOn(courseService, 'getAll').mockReturnValue(of(mockCourses));

    const fixture = TestBed.createComponent(TeacherDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('devrait être initialisé et charger la liste des cours', () => {
    expect(component).toBeTruthy();
    expect(component.courses().length).toBe(2);
    expect(component.isLoading()).toBe(false);
  });

  it('devrait filtrer les cours par recherche textuelle, matière et niveau', () => {
    // 1. Filtrer par texte
    component.searchFilter.set('Gaulois');
    expect(component.filteredCourses().length).toBe(1);
    expect(component.filteredCourses()[0].title).toBe('Les Gaulois et les Romains');

    // 2. Filtrer par matière
    component.searchFilter.set('');
    component.subjectFilter.set('Sciences');
    expect(component.filteredCourses().length).toBe(1);
    expect(component.filteredCourses()[0].subject).toBe('Sciences');

    // 3. Filtrer par niveau
    component.subjectFilter.set('ALL');
    component.gradeFilter.set('CM1');
    expect(component.filteredCourses().length).toBe(1);
    expect(component.filteredCourses()[0].grade_level).toBe('CM1');
  });

  it('devrait refuser les fichiers non PDF', () => {
    const fakeTextFile = new File(['hello'], 'cours.txt', { type: 'text/plain' });
    const event = {
      target: {
        files: [fakeTextFile],
      },
    } as unknown as Event;

    component.onFileSelected(event);
    expect(component.selectedFile()).toBeNull();
    expect(component.errorMessage()).toContain('PDF');
  });

  it("devrait accepter un fichier PDF valide et mettre à jour le signal de fichier", () => {
    const fakePdf = new File(['dummy pdf'], 'lecon.pdf', { type: 'application/pdf' });
    const event = {
      target: {
        files: [fakePdf],
      },
    } as unknown as Event;

    component.onFileSelected(event);
    expect(component.selectedFile()).toBe(fakePdf);
    expect(component.selectedFileName()).toBe('lecon.pdf');
  });

  it("devrait exécuter le flux complet d'import PDF (création, indexation RAG, génération)", () => {
    const newCourse: CourseResponse = {
      id: 3,
      title: 'La Forêt Tropicale',
      subject: 'Sciences',
      grade_level: 'CE2',
      teacher_id: 5,
      created_at: new Date().toISOString(),
      topics: [],
    };

    const enrichedCourse: CourseResponse = {
      ...newCourse,
      topics: [
        {
          id: 30,
          course_id: 3,
          name: 'La Forêt Tropicale',
          summary_kid: 'Une forêt dense et pleine de vie.',
          created_at: new Date().toISOString(),
        },
      ],
    };

    const fakePdf = new File(['dummy content'], 'foret.pdf', { type: 'application/pdf' });
    component.selectedFile.set(fakePdf);

    component.courseForm.setValue({
      title: 'La Forêt Tropicale',
      subject: 'Sciences',
      grade_level: 'CE2',
      description: 'Découverte de la canopée',
    });

    vi.spyOn(courseService, 'create').mockReturnValue(of(newCourse));
    vi.spyOn(module2Service, 'ingest').mockReturnValue(of({ chunks_indexed: 5 }));
    vi.spyOn(module2Service, 'generate').mockReturnValue(
      of({
        topic: { id: 30, course_id: 3, name: 'La Forêt', summary_kid: 'Résumé' },
        flashcards: [],
        glossary: [],
        sources: [],
      })
    );
    vi.spyOn(courseService, 'getById').mockReturnValue(of(enrichedCourse));

    component.onSubmitCourse();

    expect(courseService.create).toHaveBeenCalled();
    expect(module2Service.ingest).toHaveBeenCalledWith(3, fakePdf);
    expect(module2Service.generate).toHaveBeenCalledWith(3, 'La Forêt Tropicale', 8);
    expect(component.courses().some((c) => c.id === 3)).toBe(true);
    expect(component.successMessage()).toContain('La Forêt Tropicale');
    expect(component.selectedFile()).toBeNull();
  });

  it('devrait ouvrir la modale et supprimer un cours avec confirmation sécurisée', () => {
    const courseToDelete = mockCourses[0];
    component.openDeleteModal(courseToDelete);
    expect(component.courseToDelete()).toBe(courseToDelete);

    vi.spyOn(courseService, 'delete').mockReturnValue(of(void 0));

    component.confirmDelete();

    expect(courseService.delete).toHaveBeenCalledWith(courseToDelete.id);
    expect(component.courses().some((c) => c.id === courseToDelete.id)).toBe(false);
    expect(component.courseToDelete()).toBeNull();
    expect(component.successMessage()).toContain('supprimé');
  });
});
