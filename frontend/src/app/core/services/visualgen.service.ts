import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface ImageGenRequest {
  prompt: string;
  style: string;
  educational_level: string;
  seed?: number;
}

export interface ImageGenResponse {
  id: string;
  status: string;
  url: string;
  prompt: string;
  style: string;
  level: string;
  created_at: string;
  generation_time_s?: number;
}

export interface PromptTemplate {
  id: string;
  label: string;
  prompt: string;
}

@Injectable({ providedIn: 'root' })
export class VisualGenService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/visualgen`;

  generateImage(req: ImageGenRequest): Observable<ImageGenResponse> {
    return this.http.post<ImageGenResponse>(`${this.base}/generate`, req);
  }

  getGallery(): Observable<ImageGenResponse[]> {
    return this.http.get<ImageGenResponse[]>(`${this.base}/images`);
  }

  deleteImage(id: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/images/${id}`);
  }

  getTemplates(): Observable<PromptTemplate[]> {
    return this.http.get<PromptTemplate[]>(`${this.base}/templates`);
  }

  getImageUrl(id: string): string {
    return `${this.base}/images/${id}`;
  }
}
