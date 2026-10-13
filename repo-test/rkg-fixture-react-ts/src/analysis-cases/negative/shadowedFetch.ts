// Expected: do not classify this local function as the global Fetch API or an HTTP technology.
function fetch(value: string): string { return `local:${value}`; }
export const callShadowedFetch = (value: string): string => fetch(value);
