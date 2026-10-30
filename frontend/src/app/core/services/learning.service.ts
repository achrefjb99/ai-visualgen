import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';

export interface LearningSource { id: number; label: string; score: number; text: string; }
export interface TutorReply { answer: string; sources: LearningSource[]; redirected: boolean; badges: string[]; generation_mode?: 'ai' | 'local'; }
export interface QuizQuestion { type: 'mcq' | 'true_false' | 'short'; question: string; options: string[]; answer: string; explanation: string; }
export interface QuizSet { topic: string; questions: QuizQuestion[]; sources: LearningSource[]; generation_mode?: 'ai' | 'local'; }
export interface QuizGrade { attempt_id: number; points: number; results: { correct: boolean; points: number; feedback: string; answer: string }[]; weak_spots: string[]; boosters: string[]; badges: string[]; }
export interface ProgressReport { course_id: number; attempts: number; points: number; accuracy: number; encouragement: string; recommendation: string; superpowers: { topic: string; accuracy: number }[]; needs_practice: { topic: string; accuracy: number }[]; recent_attempts: { id: number; topic: string; points: number; correct_count: number; question_count: number; created_at: string }[]; }
export interface VisualSchema { id: number; title: string; steps: { label: string; detail: string }[]; mind_map: { label: string; children: string[] }[]; sources: LearningSource[]; created_at: string; generation_mode?: 'ai' | 'local'; }
export interface VisualGalleryItem { id: number; topic: string; title: string; content: VisualSchema; created_at: string; }

@Injectable({ providedIn: 'root' })
export class LearningService {
  private readonly http = inject(HttpClient);
  private readonly api = `${environment.apiUrl.replace(/\/+$/, '')}`;

  chatStreamUrl(): string { return `${this.api}/tutor/chat/stream`; }
  quiz(course_id: number, topic: string, difficulty: string, count: number) {
    return this.http.post<QuizSet>(`${this.api}/assessment/quiz`, { course_id, topic, difficulty, count });
  }
  grade(course_id: number, child_id: number | null, topic: string, questions: QuizQuestion[], answers: string[]) {
    return this.http.post<QuizGrade>(`${this.api}/assessment/quiz/grade`, { course_id, child_id, topic, questions, answers });
  }
  progress(courseId: number, childId: number | null) {
    const params = childId === null ? undefined : { child_id: childId };
    return this.http.get<ProgressReport>(`${this.api}/assessment/progress/${courseId}`, { params });
  }
  visual(course_id: number, topic: string) {
    return this.http.post<VisualSchema>(`${this.api}/visuals/schema`, { course_id, topic });
  }
  gallery(courseId: number) {
    return this.http.get<VisualGalleryItem[]>(`${this.api}/visuals/gallery/${courseId}`);
  }
}
