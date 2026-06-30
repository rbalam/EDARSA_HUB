import React, { useMemo, useState } from 'react';
import { CheckCircle2, Eye, EyeOff, XCircle } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

export const PASSWORD_POLICY = {
  minLength: 8,
  maxLength: 128,
  requiresUppercase: true,
  requiresLowercase: true,
  requiresNumber: true,
  requiresSpecial: false
};

export const evaluatePasswordPolicy = (password = '', confirmPassword = null) => {
  const value = password || '';
  return {
    minLength: value.length >= PASSWORD_POLICY.minLength,
    maxLength: value.length <= PASSWORD_POLICY.maxLength,
    hasUppercase: /[A-Z]/.test(value),
    hasLowercase: /[a-z]/.test(value),
    hasNumber: /[0-9]/.test(value),
    passwordsMatch: confirmPassword === null || (value.length > 0 && value === confirmPassword)
  };
};

export const isPasswordPolicySatisfied = (
  password = '',
  { required = true, confirmPassword = null } = {}
) => {
  if (!required && !password) return true;
  const checks = evaluatePasswordPolicy(password, confirmPassword);
  return (
    checks.minLength &&
    checks.maxLength &&
    checks.hasUppercase &&
    checks.hasLowercase &&
    checks.hasNumber &&
    checks.passwordsMatch
  );
};

export function PasswordInput({
  id,
  value,
  onChange,
  placeholder = '••••••••',
  disabled = false,
  required = false,
  className,
  inputClassName,
  leftIcon = null,
  'data-testid': dataTestId,
  ...props
}) {
  const [visible, setVisible] = useState(false);
  const toggleLabel = visible ? 'Ocultar contraseña' : 'Mostrar contraseña';

  return (
    <div className={cn('relative', className)}>
      {leftIcon && (
        <div className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
          {leftIcon}
        </div>
      )}
      <Input
        id={id}
        type={visible ? 'text' : 'password'}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        disabled={disabled}
        required={required}
        className={cn(leftIcon ? 'pl-10' : '', 'pr-10', inputClassName)}
        data-testid={dataTestId}
        {...props}
      />
      <button
        type="button"
        onClick={() => setVisible((current) => !current)}
        disabled={disabled}
        className="absolute right-2 top-1/2 flex h-7 w-7 -translate-y-1/2 items-center justify-center rounded-md text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
        aria-label={toggleLabel}
        title={toggleLabel}
      >
        {visible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
      </button>
    </div>
  );
}

export function PasswordRules({
  password = '',
  confirmPassword = null,
  showConfirm = false,
  className,
  compact = false
}) {
  const checks = useMemo(
    () => evaluatePasswordPolicy(password, confirmPassword),
    [password, confirmPassword]
  );

  const rules = [
    {
      key: 'length',
      valid: checks.minLength && checks.maxLength,
      text: '8 a 128 caracteres'
    },
    {
      key: 'uppercase',
      valid: checks.hasUppercase,
      text: 'Al menos una mayúscula'
    },
    {
      key: 'lowercase',
      valid: checks.hasLowercase,
      text: 'Al menos una minúscula'
    },
    {
      key: 'number',
      valid: checks.hasNumber,
      text: 'Al menos un número'
    },
    {
      key: 'special',
      valid: true,
      text: 'Carácter especial: no requerido'
    }
  ];

  if (showConfirm) {
    rules.push({
      key: 'match',
      valid: checks.passwordsMatch,
      text: 'Las contraseñas coinciden'
    });
  }

  return (
    <div className={cn('rounded-md border border-slate-200 bg-slate-50 p-3', className)}>
      {!compact && (
        <p className="mb-2 text-sm font-medium text-slate-700">Reglas de contraseña</p>
      )}
      <div className="space-y-1.5">
        {rules.map((rule) => (
          <div key={rule.key} className="flex items-center gap-2 text-sm">
            {rule.valid ? (
              <CheckCircle2 className="h-4 w-4 flex-shrink-0 text-emerald-600" />
            ) : (
              <XCircle className="h-4 w-4 flex-shrink-0 text-slate-400" />
            )}
            <span className={rule.valid ? 'text-slate-700' : 'text-slate-500'}>
              {rule.text}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
