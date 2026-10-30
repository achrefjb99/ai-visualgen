import { Component, inject, signal } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { timeout } from 'rxjs';
import { CourseIndexStatus, IngestResponse, LessonMaterial, Module2Service } from '../../../core/services/module2.service';
import { CourseResponse } from '../../../core/models/course.model';
import { CourseService } from '../../../core/services/course.service';
import { TimeoutError } from 'rxjs';

@Component({
  selector: 'app-lesson-flashcards',
  standalone: true,
  imports: [FormsModule, RouterLink],
  templateUrl: './lesson-flashcards.component.html',
  styleUrl: './lesson-flashcards.component.scss',
})
export class LessonFlashcardsComponent {
  private readonly api = inject(Module2Service);
  private readonly courseService = inject(CourseService);
  private readonly route = inject(ActivatedRoute);

  /** Id de l'enfant venu de la page d'accueil (pour le bouton retour). */
  childId = this.route.snapshot.queryParamMap.get('child');

  // Champs du formulaire
  courseId = 1;
  name = "Le cycle de l'eau";
  age = 10;
  file: File | null = null;

  // État de la page (signals : l'écran se met toujours à jour)
  readonly loading = signal<boolean>(false);
  readonly message = signal<string>('');
  readonly error = signal<string>('');
  readonly result = signal<LessonMaterial | null>(null);
  readonly flipped = signal<Set<number>>(new Set());
  readonly indexed = signal<boolean>(false);
  readonly indexedChunks = signal<number>(0);
  readonly courses = signal<CourseResponse[]>([]);
  readonly coursesLoading = signal<boolean>(true);

  ngOnInit() {
    this.courseService.getAll({ offset: 0, limit: 100 }).subscribe({
      next: (courses: CourseResponse[]) => {
        this.courses.set(courses);
        if (courses.length && !courses.some((course) => course.id === Number(this.courseId))) {
          this.courseId = courses[0].id;
        }
        this.coursesLoading.set(false);
        this.checkIndex();
      },
      error: (error: Error) => {
        this.coursesLoading.set(false);
        this.error.set(error.message || 'Impossible de charger les cours. Vérifie la connexion au serveur.');
        this.checkIndex();
      },
    });
  }

  selectCourse(event: Event) {
    const id = Number((event.target as HTMLSelectElement).value);
    if (!Number.isInteger(id) || id < 1) return;
    this.courseId = id;
    this.result.set(null);
    this.checkIndex();
  }

  checkIndex() {
    const id = Number(this.courseId);
    if (!Number.isInteger(id) || id < 1) {
      this.indexed.set(false);
      this.indexedChunks.set(0);
      return;
    }
    this.api.indexStatus(id).subscribe({
      next: (status: CourseIndexStatus) => {
        this.indexed.set(status.indexed);
        this.indexedChunks.set(status.chunks);
      },
      error: () => {
        this.indexed.set(false);
        this.indexedChunks.set(0);
      },
    });
  }

  onFile(e: Event) {
    this.file = (e.target as HTMLInputElement).files?.[0] ?? null;
  }

  flip(id: number) {
    this.flipped.update((s) => {
      const next = new Set(s);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  }

  private start() {
    this.loading.set(true);
    this.error.set('');
    this.message.set('');
  }

  private fail(err: unknown) {
    this.loading.set(false);
    if (err instanceof TimeoutError) {
      this.error.set('Le serveur met trop de temps à répondre. Réessaie dans un instant.');
      return;
    }
    if (err instanceof HttpErrorResponse) {
      const detail: unknown = err.error?.detail;
      this.error.set(typeof detail === 'string' ? detail : err.status === 0 ? 'Le serveur API est inaccessible.' : 'Erreur de connexion au serveur.');
      return;
    }
    this.error.set(err instanceof Error ? err.message : 'Erreur de connexion au serveur.');
  }

  createCourse() {
    this.start();
    this.api.createCourse('Cours test', 'Sciences', 'CM1').pipe(timeout(30000)).subscribe({
      next: (c: CourseResponse) => {
        this.loading.set(false);
        this.courseId = c.id;
        this.courses.update((courses) => [c, ...courses.filter((course) => course.id !== c.id)]);
        this.message.set(`Cours créé (numéro ${c.id})`);
        this.checkIndex();
      },
      error: (e: unknown) => this.fail(e),
    });
  }

  ingest() {
    if (!this.file) return;
    this.start();
    this.api.ingest(this.courseId, this.file).pipe(timeout(90000)).subscribe({
      next: (r: IngestResponse) => {
        this.loading.set(false);
        this.message.set(`✅ ${r.chunks_indexed} morceaux indexés`);
        this.checkIndex();
      },
      error: (e: unknown) => this.fail(e),
    });
  }

  generate() {
    if (!this.indexed()) {
      this.error.set('Crée ou sélectionne un cours, puis indexe le PDF avant de générer la leçon.');
      return;
    }
    this.start();
    this.result.set(null);
    this.flipped.set(new Set());
    this.api.generate(this.courseId, this.name, this.age).pipe(timeout(90000)).subscribe({
      next: (r: LessonMaterial) => {
        this.loading.set(false);
        this.result.set(r);
        this.message.set(r.generation_mode === 'local'
          ? 'Leçon créée à partir du cours avec le mode local. Configure Gemini pour activer la génération IA.'
          : 'Leçon générée à partir de ton cours.');
      },
      error: (e: unknown) => this.fail(e),
    });
  }
}
