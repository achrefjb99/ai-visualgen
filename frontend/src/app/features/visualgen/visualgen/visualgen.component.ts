import {
  Component, inject, OnInit, signal, computed
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink, ActivatedRoute } from '@angular/router';
import {
  VisualGenService, ImageGenRequest, ImageGenResponse, PromptTemplate
} from '../../../core/services/visualgen.service';

@Component({
  selector: 'app-visualgen',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './visualgen.component.html',
  styleUrls: ['./visualgen.component.scss'],
})
export class VisualGenComponent implements OnInit {
  private readonly svc = inject(VisualGenService);
  private readonly route = inject(ActivatedRoute);

  // ── state ──
  prompt        = signal('');
  selectedStyle = signal('cartoon');
  selectedLevel = signal('primary');
  status        = signal<'idle' | 'generating' | 'done' | 'error'>('idle');
  errorMsg      = signal('');
  lastImage     = signal<ImageGenResponse | null>(null);
  gallery       = signal<ImageGenResponse[]>([]);
  templates     = signal<PromptTemplate[]>([]);
  childId       = signal<number | null>(null);

  readonly isGenerating = computed(() => this.status() === 'generating');

  styles = [
    { value: 'cartoon',   label: '🎨 Cartoon',         desc: 'Coloré et amusant' },
    { value: 'storybook', label: '📖 Livre illustré',   desc: 'Chaleureux et magique' },
    { value: 'watercolor',label: '🖌️ Aquarelle',        desc: 'Doux et artistique' },
    { value: 'comic',     label: '💥 Bande dessinée',   desc: 'Dynamique et expressif' },
    { value: 'diagram',   label: '📐 Schéma éducatif', desc: 'Clair et informatif' },
  ];

  levels = [
    { value: 'primary', label: '🌟 École primaire',  desc: '6–10 ans' },
    { value: 'middle',  label: '🚀 Collège',          desc: '11–14 ans' },
  ];

  // ── lifecycle ──
  ngOnInit(): void {
    this.childId.set(Number(this.route.snapshot.queryParams['child']) || null);
    this.svc.getTemplates().subscribe(t => this.templates.set(t));
    this.loadGallery();
  }

  loadGallery(): void {
    this.svc.getGallery().subscribe({
      next: images => this.gallery.set(images),
      error: () => {},
    });
  }

  applyTemplate(t: PromptTemplate): void {
    this.prompt.set(t.prompt);
  }

  generate(): void {
    if (!this.prompt().trim()) return;
    this.status.set('generating');
    this.errorMsg.set('');

    const req: ImageGenRequest = {
      prompt: this.prompt(),
      style: this.selectedStyle(),
      educational_level: this.selectedLevel(),
    };

    this.svc.generateImage(req).subscribe({
      next: img => {
        this.lastImage.set(img);
        this.status.set('done');
        this.loadGallery();
      },
      error: err => {
        this.errorMsg.set(
          err?.error?.detail ?? 'Erreur lors de la génération. Réessaie !'
        );
        this.status.set('error');
      },
    });
  }

  regenerate(): void {
    this.status.set('idle');
    this.generate();
  }

  downloadImage(img: ImageGenResponse): void {
    const url = this.svc.getImageUrl(img.id);
    const a = document.createElement('a');
    a.href = url;
    a.download = `edugenius-${img.id}.png`;
    a.click();
  }

  deleteImage(id: string): void {
    this.svc.deleteImage(id).subscribe({
      next: () => {
        this.gallery.set(this.gallery().filter(i => i.id !== id));
        if (this.lastImage()?.id === id) this.lastImage.set(null);
      },
      error: () => {},
    });
  }

  getImageUrl(id: string): string {
    return this.svc.getImageUrl(id);
  }
}
