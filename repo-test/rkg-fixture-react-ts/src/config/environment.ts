export interface Environment {
  apiBaseUrl: string;
  enableAdmin: boolean;
}

type EnvironmentSource = Record<string, string | boolean | undefined>;

export function parseEnvironment(source: EnvironmentSource): Environment {
  const rawBaseUrl = source.VITE_API_BASE_URL;
  const apiBaseUrl = typeof rawBaseUrl === 'string' ? rawBaseUrl.trim().replace(/\/$/, '') : '';

  if (!apiBaseUrl) {
    throw new Error('VITE_API_BASE_URL is required');
  }

  const rawEnableAdmin = source.VITE_ENABLE_ADMIN;
  if (!['true', 'false', true, false, undefined].includes(rawEnableAdmin)) {
    throw new Error('VITE_ENABLE_ADMIN must be true or false');
  }

  return { apiBaseUrl, enableAdmin: rawEnableAdmin === true || rawEnableAdmin === 'true' };
}

export function getEnvironment(): Environment {
  return parseEnvironment(import.meta.env);
}
