let busy = false;

export function isBusy() {
    return busy;
}

export async function withRequest<T>(action: () => Promise<T>): Promise<T> {
    const controls = document.querySelectorAll<HTMLButtonElement | HTMLInputElement>('[data-request-control]');
    busy = true;
    controls.forEach(control => { control.disabled = true; });
    try {
        return await action();
    } finally {
        busy = false;
        controls.forEach(control => { control.disabled = false; });
    }
}

export function errorMessage(error: unknown) {
    return error instanceof Error ? error.message : 'Не удалось выполнить действие. Попробуйте ещё раз.';
}
