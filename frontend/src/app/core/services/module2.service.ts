import { HttpClient } from '@angular/common/http';
import { inject, Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import { CourseResponse } from '../models/course.model';

const API = environment.apiUrl;

export interface IngestResponse { chunks_indexed: number; }
export interface LessonMaterial {
  topic: { id: number; course_id: number; name: string; summary_kid: string };
  flashcards: { id: number; topic_id: number; question: string; answer: string; image_hint?: string | null }[];
  glossary: { id: number; topic_id: number; word: string; definition: string }[];
  sources: { id: number; score: number; extrait: string }[];
  generation_mode?: 'ai' | 'local';
}
export interface CourseIndexStatus { course_id: number; chunks: number; indexed: boolean; }

@Injectable({ providedIn: 'root' })
export class Module2Service {
  private readonly http = inject(HttpClient);

  createCourse(title: string, subject: string, grade_level: string): Observable<CourseResponse> {
    return this.http.post<CourseResponse>(`${API}/courses/`, { title, subject, grade_level });
  }

  ingest(courseId: number, file: File): Observable<IngestResponse> {
    const fd = new FormData();
    fd.append('course_id', String(courseId));
    fd.append('file', file);
    return this.http.post<IngestResponse>(`${API}/module2/ingest`, fd);
  }

  indexStatus(courseId: number): Observable<CourseIndexStatus> {
    return this.http.get<CourseIndexStatus>(
      `${API}/module2/courses/${courseId}/index`,
    );
  }

  generate(courseId: number, chapter: string, age: number): Observable<LessonMaterial> {
    const fd = new FormData();
    fd.append('course_id', String(courseId));
    fd.append('chapter', chapter.trim());
    fd.append('age', String(age));
    return this.http.post<LessonMaterial>(`${API}/module2/generate`, fd);
  }
}
