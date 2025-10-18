const DEFAULT_API_BASE = "/api";

const normalizeBoolean = (value: string | undefined, defaultValue: boolean) => {
  if (value === undefined) {
    return defaultValue;
  }

  return ["1", "true", "yes", "on"].includes(value.toLowerCase());
};

export const env = {
  apiBaseUrl: import.meta.env.VITE_API_URL ?? DEFAULT_API_BASE,
  useMocks: normalizeBoolean(import.meta.env.VITE_USE_MOCKS, false),
};
