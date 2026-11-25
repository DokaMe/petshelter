export function element<T extends Element>(selector: string, type: new () => T): T {
    const node = document.querySelector(selector);
    if (!(node instanceof type)) throw new Error(`Элемент ${selector} не найден`);
    return node;
}

const steps = document.querySelectorAll('.steps li');

export function setStep(id: string) {
    for (const step of steps) {
        const active = step.id === id;
        step.classList.toggle('active', active);
        if (active) step.setAttribute('aria-current', 'step');
        else step.removeAttribute('aria-current');
    }
}
