import type { Frame, Locator, Page } from "playwright";

export type QueryRoot = Page | Frame | Locator;
export type LocatorFactory = (root: QueryRoot) => Locator;

export function escapeRegex(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export async function findFirstVisible(
  root: QueryRoot,
  candidates: LocatorFactory[],
  timeoutMs = 1500,
): Promise<Locator | null> {
  for (const candidate of candidates) {
    const locator = candidate(root);

    try {
      const count = await locator.count();

      for (let index = 0; index < Math.min(count, 8); index += 1) {
        const current = locator.nth(index);

        if (await current.isVisible({ timeout: timeoutMs })) {
          return current;
        }
      }
    } catch {
      // Try the next locator candidate.
    }
  }

  return null;
}

export async function clickFirstVisible(
  root: QueryRoot,
  description: string,
  candidates: LocatorFactory[],
  timeoutMs = 1500,
): Promise<void> {
  const locator = await findFirstVisible(root, candidates, timeoutMs);

  if (!locator) {
    throw new Error(`${description} was not found in the current Omada page.`);
  }

  await locator.click();
}

export async function fillFirstVisible(
  root: QueryRoot,
  description: string,
  value: string,
  candidates: LocatorFactory[],
  timeoutMs = 1500,
): Promise<void> {
  const locator = await findFirstVisible(root, candidates, timeoutMs);

  if (!locator) {
    throw new Error(`${description} input was not found in the current Omada page.`);
  }

  await locator.fill("");
  await locator.fill(value);
}
