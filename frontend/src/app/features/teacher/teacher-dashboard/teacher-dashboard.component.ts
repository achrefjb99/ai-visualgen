import { CommonModule } from '@angular/common';
import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { CourseCreateDto, CourseResponse } from '../../../core/models/course.model';
import { AuthService } from '../../../core/services/auth.service';
import { CourseService } from '../../../core/services/course.service';
import { IngestResponse, LessonMaterial, Module2Service } from '../../../core/services/module2.service';

export interface SubjectOption {
  label: string;
  badgeBg: string;
  badgeText: string;
}

export const SUBJECT_OPTIONS: Record<string, SubjectOption> = {
  Sciences: { label: 'Sciences', badgeBg: 'bg-sky-100', badgeText: 'text-sky-800' },
  Histoire: { label: 'Histoire', badgeBg: 'bg-amber-100', badgeText: 'text-amber-800' },
  Géographie: { label: 'Géographie', badgeBg: 'bg-emerald-100', badgeText: 'text-emerald-800' },
  Français: { label: 'Français', badgeBg: 'bg-purple-100', badgeText: 'text-purple-800' },
  Mathématiques: { label: 'Mathématiques', badgeBg: 'bg-rose-100', badgeText: 'text-rose-800' },
  SVT: { label: 'SVT', badgeBg: 'bg-teal-100', badgeText: 'text-teal-800' },
};

export const GRADE_LEVELS = ['CP', 'CE1', 'CE2', 'CM1', 'CM2', '6ème'];

@Component({
  selector: 'app-teacher-dashboard',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './teacher-dashboard.component.html',
})
export class TeacherDashboardComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly courseService = inject(CourseService);
  private readonly module2Service = inject(Module2Service);
  readonly authService = inject(AuthService);

  // Signaux d'état des cours et de l'interface
  readonly courses = signal<CourseResponse[]>([]);
  readonly isLoading = signal<boolean>(true);
  readonly isUploading = signal<boolean>(false);
  readonly uploadStep = signal<string>('');
  readonly successMessage = signal<string>('');
  readonly errorMessage = signal<string>('');

  // Signal pour la suppression sécurisée
  readonly courseToDelete = signal<CourseResponse | null>(null);
  readonly isDeleting = signal<boolean>(false);

  // Signaux de filtres et recherche
  readonly searchFilter = signal<string>('');
  readonly subjectFilter = signal<string>('ALL');
  readonly gradeFilter = signal<string>('ALL');

  // Fichier sélectionné pour l'upload PDF
  readonly selectedFile = signal<File | null>(null);
  readonly selectedFileName = computed(() => this.selectedFile()?.name || '');
  readonly selectedFileSize = computed(() => {
    const file = this.selectedFile();
    if (!file) return '';
    const kb = Math.round(file.size / 1024);
    return kb > 1024 ? `${(kb / 1024).toFixed(1)} Mo` : `${kb} Ko`;
  });

  readonly availableSubjects = Object.keys(SUBJECT_OPTIONS);
  readonly availableGrades = GRADE_LEVELS;

  // Formulaire d'ajout de cours et d'import PDF
  courseForm: FormGroup = this.fb.group({
    title: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(150)]],
    subject: ['Sciences', [Validators.required]],
    grade_level: ['CE2', [Validators.required]],
    description: [''],
  });

  // Liste filtrée réactive des cours
  readonly filteredCourses = computed(() => {
    const query = this.searchFilter().trim().toLowerCase();
    const subj = this.subjectFilter();
    const gr = this.gradeFilter();

    return this.courses().filter((c) => {
      const matchQuery =
        !query ||
        c.title.toLowerCase().includes(query) ||
        c.subject.toLowerCase().includes(query) ||
        (c.topics && c.topics.some((t) => t.summary_kid?.toLowerCase().includes(query)));

      const matchSubject = subj === 'ALL' || c.subject === subj;
      const matchGrade = gr === 'ALL' || c.grade_level === gr;

      return matchQuery && matchSubject && matchGrade;
    });
  });

  ngOnInit(): void {
    this.loadCourses();
  }

  loadCourses(): void {
    this.isLoading.set(true);
    this.errorMessage.set('');

    const currentTeacherId = this.authService.currentUser()?.id;
    // Si l'utilisateur est enseignant, on filtre par son identifiant
    const filter = currentTeacherId ? { teacher_id: currentTeacherId, limit: 100 } : { limit: 100 };

    this.courseService.getAll(filter).subscribe({
      next: (data) => {
        this.courses.set(data);
        this.isLoading.set(false);
      },
      error: (err) => {
        this.errorMessage.set(
          err?.error?.detail || 'Impossible de récupérer la liste des cours pour le moment.'
        );
        this.isLoading.set(false);
      },
    });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files && input.files.length > 0) {
      const file = input.files[0];
      if (file.type !== 'application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) {
        this.errorMessage.set('Le fichier sélectionné doit être un document PDF valide.');
        this.selectedFile.set(null);
        return;
      }
      this.selectedFile.set(file);
      this.errorMessage.set('');
    }
  }

  clearSelectedFile(): void {
    this.selectedFile.set(null);
  }

  onSubmitCourse(): void {
    if (this.courseForm.invalid) {
      this.courseForm.markAllAsTouched();
      return;
    }

    const file = this.selectedFile();
    if (!file) {
      this.errorMessage.set('Veuillez sélectionner un fichier PDF de cours avant de valider.');
      return;
    }

    const formValues = this.courseForm.value;
    const dto: CourseCreateDto = {
      title: formValues.title.trim(),
      subject: formValues.subject,
      grade_level: formValues.grade_level,
      description: formValues.description?.trim() || null,
    };

    this.isUploading.set(true);
    this.errorMessage.set('');
    this.successMessage.set('');
    this.uploadStep.set('1/3 - Enregistrement du cours...');

    // 1. Création du cours dans la base
    this.courseService.create(dto).subscribe({
      next: (createdCourse) => {
        this.uploadStep.set('2/3 - Extraction et indexation du PDF (RAG)...');

        // 2. Indexation du PDF
        this.module2Service.ingest(createdCourse.id, file).subscribe({
          next: (_ingestRes: IngestResponse) => {
            this.uploadStep.set('3/3 - Génération du résumé adapté au niveau...');

            const targetAge = this.resolveAgeFromGrade(createdCourse.grade_level);

            // 3. Génération du résumé & des premières fiches
            this.module2Service.generate(createdCourse.id, createdCourse.title, targetAge).subscribe({
              next: (_material: LessonMaterial) => {
                this.finalizeUpload(createdCourse.id, createdCourse.title);
              },
              error: () => {
                // Même si la génération IA échoue ou est hors-ligne, le cours et le PDF sont bien enregistrés
                this.finalizeUpload(createdCourse.id, createdCourse.title);
              },
            });
          },
          error: (ingestErr) => {
            this.isUploading.set(false);
            this.errorMessage.set(
              ingestErr?.error?.detail ||
                "Erreur lors de l'indexation du PDF. Le document a peut-être un format protégé."
            );
            // Recharger la liste pour afficher au moins le cours créé
            this.loadCourses();
          },
        });
      },
      error: (createErr) => {
        this.isUploading.set(false);
        this.errorMessage.set(
          createErr?.error?.detail || 'Erreur lors de la création du cours.'
        );
      },
    });
  }

  private finalizeUpload(courseId: number, courseTitle: string): void {
    // Recharger le cours complet avec ses topics générés
    this.courseService.getById(courseId).subscribe({
      next: (fullCourse) => {
        this.courses.update((list) => [fullCourse, ...list.filter((c) => c.id !== courseId)]);
        this.finishSuccess(courseTitle);
      },
      error: () => {
        this.loadCourses();
        this.finishSuccess(courseTitle);
      },
    });
  }

  private finishSuccess(courseTitle: string): void {
    this.isUploading.set(false);
    this.uploadStep.set('');
    this.selectedFile.set(null);
    this.courseForm.reset({
      title: '',
      subject: 'Sciences',
      grade_level: 'CE2',
      description: '',
    });
    this.successMessage.set(
      `Le cours « ${courseTitle} » a été publié et analysé avec succès !`
    );
  }

  // --- Suppression de cours sécurisée avec modale ---

  openDeleteModal(course: CourseResponse): void {
    this.courseToDelete.set(course);
  }

  closeDeleteModal(): void {
    if (!this.isDeleting()) {
      this.courseToDelete.set(null);
    }
  }

  confirmDelete(): void {
    const course = this.courseToDelete();
    if (!course) return;

    this.isDeleting.set(true);
    this.errorMessage.set('');

    this.courseService.delete(course.id).subscribe({
      next: () => {
        this.courses.update((list) => list.filter((c) => c.id !== course.id));
        this.isDeleting.set(false);
        this.courseToDelete.set(null);
        this.successMessage.set(`Le cours « ${course.title} » a été supprimé avec succès.`);
      },
      error: (err) => {
        this.isDeleting.set(false);
        this.errorMessage.set(
          err?.error?.detail || 'Impossible de supprimer ce cours. Vérifiez vos permissions.'
        );
      },
    });
  }

  getSubjectBadge(subject: string): SubjectOption {
    return (
      SUBJECT_OPTIONS[subject] || {
        label: subject,
        badgeBg: 'bg-slate-100',
        badgeText: 'text-slate-700',
      }
    );
  }

  getTopicSummary(course: CourseResponse): string {
    if (course.topics && course.topics.length > 0 && course.topics[0].summary_kid) {
      return course.topics[0].summary_kid;
    }
    return course.description || 'Aucun résumé généré pour le moment.';
  }

  formatDate(dateString: string): string {
    if (!dateString) return '';
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString('fr-FR', {
        day: '2-digit',
        month: 'short',
        year: 'numeric',
      });
    } catch {
      return dateString;
    }
  }

  private resolveAgeFromGrade(grade: string): number {
    switch (grade) {
      case 'CP':
        return 6;
      case 'CE1':
        return 7;
      case 'CE2':
        return 8;
      case 'CM1':
        return 9;
      case 'CM2':
        return 10;
      case '6ème':
        return 11;
      default:
        return 8;
    }
  }
}
