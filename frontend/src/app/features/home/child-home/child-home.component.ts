import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';
import { UserResponse } from '../../../core/models/user.model';
import { UserService } from '../../../core/services/user.service';
import { THEME_OPTIONS } from '../../auth/child-profile-manager/child-profile-manager.component';

@Component({
  selector: 'app-child-home',
  standalone: true,
  imports: [RouterLink],
  template: `<div class="p-8 text-center"><a [routerLink]="['/visualgen']" [queryParams]="{child: child()?.id}">AI VisualGen</a></div>`,
})
export class ChildHomeComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);
  private readonly userService = inject(UserService);

  readonly child = signal<UserResponse | null>(null);
  readonly isLoading = signal<boolean>(true);
  readonly error = signal<string>('');

  readonly theme = computed(
    () => THEME_OPTIONS.find((t) => t.id === this.child()?.favorite_theme) ?? THEME_OPTIONS[0]
  );
  readonly persona = computed(() => {
    const age = this.child()?.age ?? 8;
    return age <= 7 ? 'Petit explorateur' : age <= 10 ? 'Inventeur curieux' : 'Grand stratège';
  });
  readonly recommendation = computed(() => {
    const theme = this.theme().label.toLowerCase();
    const age = this.child()?.age ?? 8;
    return age <= 7
      ? `Commence par une petite histoire sur ${theme}, puis découvre tes cartes mémoire.`
      : `Choisis une leçon sur ${theme}, demande un indice à Buddy et termine par un quiz.`;
  });

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.userService.getById(id).subscribe({
      next: (c) => {
        this.child.set(c);
        this.isLoading.set(false);
      },
      error: (err: Error) => {
        this.error.set(err.message || 'Profil introuvable.');
        this.isLoading.set(false);
      },
    });
  }
}
