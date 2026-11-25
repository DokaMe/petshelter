import type { Animal, ConversationInput } from './api';

export interface Option<T> {
    label: string;
    value: T;
}

export interface Question<T> {
    text: string;
    friendText?: string;
    options: readonly Option<T>[];
}

export const purposeQuestion: Question<ConversationInput['purpose']> = {
    text: 'Вы хотите взять питомца домой или оформить опекунство?',
    friendText: 'Хочешь забрать питомца домой или стать его опекуном?',
    options: [
        { label: 'Взять домой', value: 'adoption' },
        { label: 'Оформить опеку', value: 'guardianship' },
        { label: 'Не знаю', value: 'undecided' },
    ],
};

export const housingQuestion: Question<ConversationInput['housing']> = {
    text: 'Где вы живёте?',
    friendText: 'Где ты живёшь?',
    options: [
        { label: 'В квартире', value: 'apartment' },
        { label: 'В частном доме', value: 'house' },
    ],
};

export const speciesQuestion: Question<ConversationInput['species']> = {
    text: 'Кого вы хотите завести?',
    friendText: 'Кого ты хочешь завести?',
    options: [
        { label: 'Кота', value: 'cat' },
        { label: 'Собаку', value: 'dog' },
        { label: 'Неважно', value: 'any' },
    ],
};

export const genderQuestion = {
    text: 'Какого пола питомца вы хотите завести?',
    friendText: 'Кого предпочитаешь, мальчика или девочку?',
    options: [
        { label: 'Мальчик', value: 'male' },
        { label: 'Девочка', value: 'female' },
        { label: 'Неважно', value: 'any' },
    ],
} as const;

const yesNo = [
    { label: 'Да', value: true },
    { label: 'Нет', value: false },
] as const;

export const childrenQuestion = {
    text: 'У вас есть дети?',
    friendText: 'У тебя есть дети?',
    options: yesNo,
};

export const otherPetsQuestion = {
    text: 'У вас есть домашние животные?',
    friendText: 'У тебя есть домашние животные?',
    options: yesNo,
};

export const experienceQuestion = {
    text: 'У вас были домашние животные?',
    friendText: 'У тебя раньше были домашние животные?',
    options: yesNo,
};

export const activityQuestion = {
    text: 'Какой у вас образ жизни?',
    friendText: 'Какой у тебя образ жизни?',
    options: [
        { label: 'Активный', value: 'active' },
        { label: 'Спокойный', value: 'calm' },
    ],
} as const;

export type Gender = (typeof genderQuestion.options)[number]['value'];

const animalGenders: Readonly<Record<Exclude<Gender, 'any'>, readonly string[]>> = {
    male: ['male', 'm', 'м', 'самец', 'мальчик', 'мужской', 'кот', 'кобель'],
    female: ['female', 'f', 'ж', 'самка', 'девочка', 'женский', 'кошка', 'сука'],
};

export function animalGender(value: string): Exclude<Gender, 'any'> | undefined {
    const gender = value.trim().toLowerCase();
    if (animalGenders.male.includes(gender)) return 'male';
    if (animalGenders.female.includes(gender)) return 'female';
}

export function matchesAnimal(
    animal: Animal,
    shelterId: number,
    species: ConversationInput['species'],
    gender: Gender,
): boolean {
    return animal.status === 'available'
        && animal.shelter === shelterId
        && (species === 'any' || animal.species === species)
        && (gender === 'any' || animalGender(animal.gender) === gender);
}
