import { api } from './api';
import type { CatalogAnimal } from './api';
import { element } from './dom';
import { petCard } from './pet-card';
import { errorMessage } from './request-state';

const list = element('#catalogList', HTMLDivElement);
const status = element('#catalogStatus', HTMLParagraphElement);
const retry = element('#catalogRetry', HTMLButtonElement);
let subscribe: (animal: CatalogAnimal) => void;
let requestCount = 0;

function catalogCard(animal: CatalogAnimal) {
    if (animal.status === 'adopted') return petCard(animal);

    const actions = document.createElement('div');
    actions.className = 'catalog-actions';

    const guard = document.createElement('button');
    guard.type = 'button';
    guard.className = 'catalog-subscribe';
    guard.disabled = animal.guardianship_slots < 1;
    guard.textContent = guard.disabled ? 'Все 5 мест опеки заняты' : 'Оформить опеку';
    guard.addEventListener('click', () => subscribe(animal));

    const adopt = document.createElement('button');
    adopt.type = 'button';
    adopt.className = 'catalog-adopt';
    adopt.textContent = 'Забрать домой';
    adopt.setAttribute('aria-expanded', 'false');

    const contact = document.createElement('div');
    contact.id = `adopt-contact-${animal.id}`;
    contact.className = 'adoption-contact hidden';
    contact.setAttribute('role', 'status');
    adopt.setAttribute('aria-controls', contact.id);
    adopt.addEventListener('click', async () => {
        const expanded = adopt.getAttribute('aria-expanded') === 'true';
        adopt.setAttribute('aria-expanded', String(!expanded));
        contact.classList.toggle('hidden', expanded);
        if (expanded) return;
        contact.textContent = 'Загружаем контакты приюта…';
        try {
            const shelter = (await api.shelters()).find(item => item.id === animal.shelter);
            if (!shelter) {
                contact.textContent = 'В карточке пока нет контактов приюта.';
                return;
            }
            contact.textContent = 'Для знакомства с питомцем свяжитесь с приютом.';
            const details = [shelter.city, shelter.address, shelter.phone].filter(Boolean).join(' · ');
            if (details) {
                const info = document.createElement('span');
                info.textContent = details;
                contact.append(info);
            }
        } catch (error) {
            contact.textContent = errorMessage(error);
        }
    });

    actions.append(guard, adopt, contact);
    return petCard(animal, { actions });
}

export async function refreshCatalog() {
    const request = ++requestCount;
    retry.classList.add('hidden');
    if (!list.childElementCount) status.textContent = 'Загружаем питомцев…';
    try {
        const animals = await api.animals();
        if (request !== requestCount) return;
        animals.sort((first, second) =>
            Number(first.status === 'adopted') - Number(second.status === 'adopted')
            || Number(Boolean(second.photo)) - Number(Boolean(first.photo)),
        );
        list.replaceChildren(...animals.map(catalogCard));
        status.textContent = animals.length ? '' : 'В каталоге пока нет питомцев.';
    } catch (error) {
        if (request !== requestCount) return;
        status.textContent = errorMessage(error);
        retry.classList.remove('hidden');
    }
}

export function setupCatalog(onSubscribe: (animal: CatalogAnimal) => void) {
    subscribe = onSubscribe;
    retry.addEventListener('click', () => { void refreshCatalog(); });
    void refreshCatalog();
}
