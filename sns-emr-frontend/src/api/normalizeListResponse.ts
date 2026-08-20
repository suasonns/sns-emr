export function normalizeListResponse<T>(
  payload: unknown,
  envelopeKeys: readonly string[],
  responseName: string,
): T[] {
  if (Array.isArray(payload)) {
    return payload as T[];
  }

  if (typeof payload === "object" && payload !== null) {
    const envelope = payload as Record<string, unknown>;
    for (const key of envelopeKeys) {
      if (Array.isArray(envelope[key])) {
        return envelope[key] as T[];
      }
    }
  }

  throw new TypeError(`${responseName} response did not contain a list`);
}
