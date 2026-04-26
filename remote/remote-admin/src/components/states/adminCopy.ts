export function formatAdminMissingSession(resource: string): string {
  return `Please sign in again to load ${resource}.`;
}

export function formatAdminLoadError(resource: string): string {
  return `The ${resource} could not be loaded from the admin API.`;
}

export function formatAdminListError(resource: string): string {
  return formatAdminLoadError(`${resource} list`);
}

export function formatAdminDetailError(resource: string): string {
  return formatAdminLoadError(`selected ${resource} detail`);
}

export function formatFilteredEmptyState(resource: string): string {
  return `No ${resource} matched the current filters.`;
}

export function formatSelectionEmptyState(item: string, detail: string): string {
  return `Select ${item} from the list to inspect ${detail}.`;
}
