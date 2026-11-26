import type { Animal } from './api';
import { animalGender } from './questionnaire';

interface CardOptions {
    actions?: HTMLElement;
    details?: string;
}

export function petCard(animal: Animal, { actions, details }: CardOptions = {}) {
    const card = document.createElement('article');
    card.className = 'pet-card';

    if (animal.photo) {
        const photo = document.createElement('img');
        photo.className = 'pet-card__photo';
        photo.src = animal.photo;
        photo.alt = animal.name;
        photo.loading = 'lazy';
        photo.addEventListener('error', () => photo.remove(), { once: true });
        card.append(photo);
    }

    const body = document.createElement('div');
    body.className = 'pet-card__body';

    const name = document.createElement('h3');
    name.textContent = animal.name;
    body.append(name);

    const meta = document.createElement('p');
    meta.className = 'pet-card__meta';
    const male = animalGender(animal.gender) === 'male';
    const species = animal.species === 'dog' ? (male ? 'Пёс' : 'Собака') : (male ? 'Кот' : 'Кошка');
    meta.textContent = [species, animal.age, animal.breed].filter(Boolean).join(' · ');
    body.append(meta);

    if (animal.coat_color) {
        const coat = document.createElement('p');
        coat.className = 'pet-card__meta';
        const source = animal.coat_color_source === 'photo' ? 'Окрас по фото' : 'Окрас';
        coat.textContent = `${source} · ${animal.coat_color}`;
        body.append(coat);
    }

    if (animal.shelter_name) {
        const shelter = document.createElement('p');
        shelter.className = 'pet-card__shelter';
        shelter.textContent = animal.shelter_name;
        body.append(shelter);
    }

    if (animal.description) {
        const description = document.createElement('p');
        description.className = 'pet-card__description';
        description.textContent = animal.description;
        body.append(description);
    }

    if (details || animal.status === 'adopted') {
        const status = document.createElement('p');
        status.className = 'pet-card__status';
        status.textContent = details ?? 'Уже дома';
        body.append(status);
    }

    if (actions) body.append(actions);

    card.append(body);
    return card;
}
