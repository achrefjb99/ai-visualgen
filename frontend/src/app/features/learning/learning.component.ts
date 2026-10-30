import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { HttpErrorResponse } from '@angular/common/http';
import { LearningService, ProgressReport, QuizGrade, QuizQuestion, QuizSet, TutorReply, VisualGalleryItem, VisualSchema } from '../../core/services/learning.service';
import { CourseService } from '../../core/services/course.service';
import { CourseResponse } from '../../core/models/course.model';

interface SpeechResultEvent { results: ArrayLike<ArrayLike<{ transcript: string }>>; }
interface TutorStreamEvent extends Partial<TutorReply> { text?: string; done?: boolean; }
interface SpeechRecognizer { lang: string; onresult: ((event: SpeechResultEvent) => void) | null; start(): void; }
type SpeechRecognizerConstructor = new () => SpeechRecognizer;

@Component({
  selector: 'app-learning', standalone: true, imports: [FormsModule, RouterLink, DatePipe],
  templateUrl: './learning.component.html',
})
export class LearningComponent {
  private readonly api = inject(LearningService);
  private readonly courseService = inject(CourseService);
  private readonly route = inject(ActivatedRoute);
  readonly childId = Number(this.route.snapshot.queryParamMap.get('child')) || null;
  readonly courses = signal<CourseResponse[]>([]);
  readonly mode = signal<'tutor' | 'quiz' | 'visual' | 'progress'>(this.route.snapshot.data['mode'] ?? 'tutor');
  readonly loading = signal(false); readonly error = signal(''); readonly notice = signal('');
  readonly answer = signal<TutorReply | null>(null); readonly quizData = signal<QuizSet | null>(null); readonly grade = signal<QuizGrade | null>(null); readonly visualData = signal<VisualSchema | null>(null);
  readonly progressData = signal<ProgressReport | null>(null); readonly galleryData = signal<VisualGalleryItem[]>([]);
  courseId = Number(this.route.snapshot.queryParamMap.get('course')) || 0; topic = ''; message = ''; hint = false; analogy = ''; difficulty = 'easy'; answers: string[] = [];
  ngOnInit() {
    this.courseService.getAll({ limit: 100 }).subscribe({
      next: (courses: CourseResponse[]) => {
        this.courses.set(courses);
        if (!courses.length) {
          this.error.set('Aucun cours pour le moment. Crée un cours et indexe un PDF dans le Module 2.');
          return;
        }
        if (!courses.some((course) => course.id === this.courseId)) this.courseId = courses[0].id;
        if (this.mode() === 'progress') this.loadProgress();
        if (this.mode() === 'visual') this.loadGallery();
      },
      error: (error: Error) => this.fail(error),
    });
  }
  ask() {
    if (!this.courseId) { this.error.set('Choisis un cours avant de poser une question.'); return; }
    if (!this.message.trim()) return;
    this.begin();
    const request = { course_id: Number(this.courseId), message: this.message, hint: this.hint, analogy: this.analogy };
    this.answer.set({ answer: '', sources: [], badges: [], redirected: false });
    fetch(this.api.chatStreamUrl(), { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(request) }).then(async response => {
      if (!response.ok || !response.body) { const detail = await response.json().catch(() => ({})); throw new Error(detail.detail ?? 'Le tuteur est momentanément indisponible.'); }
      const reader = response.body.getReader(); const decoder = new TextDecoder(); let pending = '';
      while (true) {
        const { value, done } = await reader.read(); if (done) break;
        pending += decoder.decode(value, { stream: true }); const events = pending.split('\n\n'); pending = events.pop() ?? '';
        for (const event of events) { const line = event.split('\n').find(part => part.startsWith('data: ')); if (!line) continue; const data = JSON.parse(line.slice(6)) as TutorStreamEvent;
          if (data.text) this.answer.update(current => current ? ({ ...current, answer: current.answer + data.text }) : current);
          if (data.done) this.answer.update(current => current ? ({ ...current, ...data } as TutorReply) : current);
        }
      }
      this.loading.set(false);
    }).catch(error => this.fail({ error: { detail: error.message } }));
  }
  speak(text: string) {
    if ('speechSynthesis' in window) { window.speechSynthesis.cancel(); window.speechSynthesis.speak(new SpeechSynthesisUtterance(text)); }
  }
  listen() {
    const speechWindow = window as Window & { SpeechRecognition?: SpeechRecognizerConstructor; webkitSpeechRecognition?: SpeechRecognizerConstructor };
    const Speech = speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition;
    if (!Speech) { this.error.set('La saisie vocale n’est pas disponible dans ce navigateur.'); return; }
    const recognition = new Speech(); recognition.lang = 'fr-FR'; recognition.onresult = (event: SpeechResultEvent) => this.message = event.results[0][0].transcript; recognition.start();
  }
  makeQuiz() {
    if (!this.courseId) { this.error.set('Choisis un cours avant de préparer un quiz.'); return; }
    if (!this.topic.trim()) { this.error.set('Écris le sujet de ta leçon pour créer le quiz.'); return; }
    this.begin(); this.grade.set(null);
    this.api.quiz(Number(this.courseId), this.topic, this.difficulty, 5).subscribe({
      next: (data: QuizSet) => { this.quizData.set(data); this.answers = data.questions.map(() => ''); this.loading.set(false); }, error: (e: HttpErrorResponse) => this.fail(e),
    });
  }
  submitQuiz() {
    const data = this.quizData(); if (!data) return;
    this.begin();
    this.api.grade(Number(this.courseId), this.childId, this.topic, data.questions, this.answers).subscribe({
      next: (result: QuizGrade) => { this.grade.set(result); this.loading.set(false); this.loadProgress(); }, error: (e: HttpErrorResponse) => this.fail(e),
    });
  }
  makeVisual() {
    if (!this.courseId) { this.error.set('Choisis un cours avant de créer un schéma.'); return; }
    if (!this.topic.trim()) { this.error.set('Écris le sujet de ta leçon pour créer le schéma.'); return; }
    this.begin(); this.api.visual(Number(this.courseId), this.topic).subscribe({
      next: (data: VisualSchema) => { this.visualData.set(data); this.loading.set(false); this.loadGallery(); }, error: (e: HttpErrorResponse) => this.fail(e),
    });
  }
  loadProgress() { this.api.progress(Number(this.courseId), this.childId).subscribe({ next: (data: ProgressReport) => this.progressData.set(data), error: () => this.progressData.set(null) }); }
  loadGallery() { this.api.gallery(Number(this.courseId)).subscribe({ next: (data: VisualGalleryItem[]) => this.galleryData.set(data), error: () => this.galleryData.set([]) }); }
  private begin() { this.loading.set(true); this.error.set(''); this.notice.set(''); }
  private fail(error: unknown) {
    this.loading.set(false);
    if (error instanceof HttpErrorResponse) {
      const detail: unknown = error.error?.detail;
      this.error.set(typeof detail === 'string' ? detail : error.status === 0 ? 'Serveur inaccessible. Vérifie que l’API EduGenius fonctionne.' : 'Le service n’a pas pu terminer cette demande. Réessaie dans un instant.');
      return;
    }
    this.error.set(error instanceof Error ? error.message : 'Une erreur de connexion au serveur est survenue.');
  }

  selectCourse(event: Event) {
    const value = (event.target as HTMLSelectElement).value;
    this.courseId = Number(value);
    this.grade.set(null);
    this.quizData.set(null);
    this.visualData.set(null);
    this.progressData.set(null);
    this.galleryData.set([]);
    if (this.mode() === 'progress') this.loadProgress();
    if (this.mode() === 'visual') this.loadGallery();
  }
}
