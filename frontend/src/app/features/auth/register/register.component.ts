import { CommonModule } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormBuilder,
  ReactiveFormsModule,
  ValidationErrors,
  ValidatorFn,
  Validators,
} from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { RegisterRequest, UserRole } from '../../../core/models/auth.model';
import { AuthService } from '../../../core/services/auth.service';

/**
 * Validateur croisé assurant que le mot de passe et sa confirmation sont strictement identiques.
 */
export const passwordMatchValidator: ValidatorFn = (
  control: AbstractControl
): ValidationErrors | null => {
  const password = control.get('password')?.value;
  const confirmPassword = control.get('confirmPassword')?.value;

  if (!password || !confirmPassword) {
    return null;
  }

  return password === confirmPassword ? null : { passwordMismatch: true };
};

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './register.component.html',
})
export class RegisterComponent {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);
  private readonly router = inject(Router);

  readonly userRoles = UserRole;
  readonly isLoading = signal<boolean>(false);
  readonly errorMessage = signal<string | null>(null);
  readonly showPassword = signal<boolean>(false);
  readonly showConfirmPassword = signal<boolean>(false);

  readonly registerForm = this.fb.nonNullable.group(
    {
      role: [UserRole.PARENT, [Validators.required]],
      username: [
        '',
        [
          Validators.required,
          Validators.minLength(3),
          Validators.maxLength(50),
          Validators.pattern(/^[a-zA-Z0-9_\-\.]+$/),
        ],
      ],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]],
    },
    { validators: [passwordMatchValidator] }
  );

  selectRole(role: UserRole): void {
    this.registerForm.patchValue({ role });
  }

  toggleShowPassword(): void {
    this.showPassword.update((v) => !v);
  }

  toggleShowConfirmPassword(): void {
    this.showConfirmPassword.update((v) => !v);
  }

  onSubmit(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }

    this.isLoading.set(true);
    this.errorMessage.set(null);

    const formVal = this.registerForm.getRawValue();
    const dto: RegisterRequest = {
      username: formVal.username.trim(),
      email: formVal.email.trim().toLowerCase(),
      password: formVal.password,
      role: formVal.role,
    };

    this.authService.register(dto).subscribe({
      next: (res) => {
        this.isLoading.set(false);
        if (res.user.role === UserRole.TEACHER) {
          this.router.navigate(['/teacher-dashboard']);
        } else {
          this.router.navigate(['/parent-dashboard']);
        }
      },
      error: (err) => {
        this.isLoading.set(false);
        if (err.error?.detail) {
          this.errorMessage.set(err.error.detail);
        } else if (err.status === 400) {
          this.errorMessage.set('Données d’inscription invalides.');
        } else {
          this.errorMessage.set('Impossible de créer le compte. Vérifie la connexion au serveur.');
        }
      },
    });
  }
}
