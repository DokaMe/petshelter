import { api } from './api';
import type { CatalogAnimal } from './api';
import { element } from './dom';
import { errorMessage, isBusy, withRequest } from './request-state';

const dialog = element('#subscriptionDialog', HTMLDialogElement);
const title = element('#subscriptionTitle', HTMLHeadingElement);
const description = element('#subscriptionDescription', HTMLParagraphElement);
const status = element('#subscriptionStatus', HTMLParagraphElement);
const form = element('#subscriptionForm', HTMLFormElement);
const payment = element('#subscriptionPay', HTMLButtonElement);
const close = element('#subscriptionClose', HTMLButtonElement);

close.addEventListener('click', () => dialog.close());
dialog.addEventListener('cancel', event => {
    if (isBusy()) event.preventDefault();
});

export function openSubscription(animal: CatalogAnimal): Promise<boolean> {
    if (isBusy() || dialog.open || animal.guardianship_slots <= 0 || animal.status !== 'available') {
        return Promise.resolve(false);
    }

    title.textContent = `Опека над питомцем «${animal.name}»`;
    description.textContent = 'Сейчас пройдёт тестовая оплата подписки. Деньги не списываются.';
    status.textContent = '';
    payment.classList.remove('hidden');
    close.textContent = 'Отмена';
    let completed = false;

    form.onsubmit = async event => {
        event.preventDefault();
        if (isBusy() || completed) return;
        status.textContent = 'Проводим тестовую оплату…';

        try {
            // Replace this demo confirmation with the payment provider when billing is enabled.
            await withRequest(() => api.registerGuardianship(animal.id));
            completed = true;
            title.textContent = 'Оплата успешно прошла';
            description.textContent = 'Тестовая подписка оформлена. Питомец добавлен в «Мои подопечные».';
            status.textContent = 'Деньги не списаны.';
            payment.classList.add('hidden');
            close.textContent = 'К подопечным';
            close.focus();
        } catch (error) {
            status.textContent = errorMessage(error);
        }
    };

    dialog.showModal();
    return new Promise(resolve => {
        dialog.addEventListener('close', () => {
            form.onsubmit = null;
            resolve(completed);
        }, { once: true });
    });
}
