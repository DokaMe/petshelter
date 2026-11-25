import { api } from './api';
import type { Animal, CatalogAnimal, ConversationInput, Shelter } from './api';
import { element, setStep } from './dom';
import { errorMessage, isBusy, withRequest } from './request-state';
import { petCard } from './pet-card';
import { showGuardianships } from './account';
import { refreshCatalog } from './catalog';
import { openSubscription } from './subscription';
import {
    activityQuestion,
    childrenQuestion,
    experienceQuestion,
    genderQuestion,
    housingQuestion,
    matchesAnimal,
    otherPetsQuestion,
    purposeQuestion,
    speciesQuestion,
} from './questionnaire';
import type { Option, Question } from './questionnaire';

const chatLog = element('#chatMessage', HTMLDivElement);
const messageForm = element('#chatInputArea', HTMLFormElement);
const messageInput = element('#userInput', HTMLInputElement);

type CommunicationStyle = ConversationInput['communication_style'];

let messageMode: 'name' | 'chat' | null = null;
let communicationStyle: CommunicationStyle = 'consultant';
let dialog = new AbortController();
let sessionId: string | null = null;

function scrollToLatest() {
    chatLog.scrollTop = chatLog.scrollHeight;
}

function revealChatItem(item: HTMLElement) {
    const top = item.getBoundingClientRect().top - chatLog.getBoundingClientRect().top;
    chatLog.scrollTop += top - 12;
}

function addMessage(text: string, sender: 'bot' | 'user', intro = false) {
    const message = document.createElement('div');
    message.classList.add('message', sender);
    message.classList.toggle('intro', intro);
    message.textContent = text;
    chatLog.append(message);
    scrollToLatest();
    return message;
}

function botSay(text: string, friendText = text) {
    return addMessage(communicationStyle === 'friend' ? friendText : text, 'bot');
}

function setMessageMode(mode: typeof messageMode) {
    messageMode = mode;
    messageForm.classList.toggle('hidden', mode === null);
    messageInput.value = '';
    messageInput.placeholder = mode === 'name' ? 'Кличка питомца…' : 'Сообщение…';
}

function chooseOption<T>(
    options: readonly Option<T>[],
    signal: AbortSignal,
    renderOption?: (option: Option<T>, button: HTMLButtonElement) => HTMLElement,
): Promise<T> {
    signal.throwIfAborted();
    const container = document.createElement('div');
    container.className = renderOption ? 'pet-list' : 'option-container';

    return new Promise((resolve, reject) => {
        const cancel = () => reject(signal.reason);
        signal.addEventListener('abort', cancel, { once: true });
        for (const option of options) {
            const button = document.createElement('button');
            button.className = 'option-btn';
            button.type = 'button';
            button.textContent = option.label;
            button.addEventListener('click', () => {
                if (isBusy() || signal.aborted) return;
                signal.removeEventListener('abort', cancel);
                button.classList.add('chose');
                container.querySelectorAll('button').forEach(item => { item.disabled = true; });
                resolve(option.value);
            });
            container.append(renderOption ? renderOption(option, button) : button);
        }
        chatLog.append(container);
        if (renderOption) revealChatItem(container);
        else scrollToLatest();
    });
}

function ask<T>(question: Question<T>, signal: AbortSignal) {
    signal.throwIfAborted();
    botSay(question.text, question.friendText);
    return chooseOption(question.options, signal);
}

function chooseAnimal(animals: CatalogAnimal[], signal: AbortSignal) {
    return chooseOption(
        animals.map(animal => ({ label: `Выбрать: ${animal.name}`, value: animal })),
        signal,
        ({ value: animal }, button) => {
            button.classList.add('pet-card__action');
            button.setAttribute('aria-label', button.textContent ?? 'Выбрать');
            button.textContent = 'Выбрать';
            return petCard(animal, { actions: button });
        },
    );
}

export async function startChat() {
    dialog.abort();
    dialog = new AbortController();
    const { signal } = dialog;
    sessionId = null;
    setMessageMode(null);
    setStep('stepSurv');
    chatLog.replaceChildren();
    try {
        communicationStyle = await ask<CommunicationStyle>({
            text: 'Как вам удобнее общаться?',
            options: [
                { label: 'Как друг', value: 'friend' },
                { label: 'Как консультант', value: 'consultant' },
            ],
        }, signal);
        botSay('Расскажите, кого ищете…', 'Давай найдём тебе питомца.').classList.add('intro');
        await showStartOptions(signal);
    } catch (error) {
        if (!signal.aborted) botSay(errorMessage(error));
    }
}

async function showStartOptions(signal: AbortSignal) {
    while (!signal.aborted) {
        sessionId = null;
        setMessageMode(null);
        setStep('stepSurv');
        try {
            const choice = await ask({
                text: 'Вы уже выбрали питомца или хотите подобрать?',
                friendText: 'Уже знаешь, кого ищешь, или помочь с выбором?',
                options: [
                    { label: 'Уже выбрал(-а)', value: 'name' },
                    { label: 'Хочу подобрать', value: 'questionnaire' },
                ],
            }, signal);
            if (choice === 'name') {
                botSay('Введите кличку питомца.', 'Напиши кличку питомца.');
                setMessageMode('name');
                messageInput.focus();
                return;
            }
            await runQuestionnaire(signal);
            return;
        } catch (error) {
            if (signal.aborted) return;
            botSay(errorMessage(error));
        }
    }
}

async function runQuestionnaire(signal: AbortSignal) {
    const shelters = await withRequest(api.shelters);
    if (!shelters.length) {
        botSay('В каталоге пока нет приютов. Попробуйте позже.', 'В каталоге пока нет приютов. Попробуй зайти позже.');
        return;
    }

    const purpose = await ask(purposeQuestion, signal);
    const species = await ask(speciesQuestion, signal);
    const gender = await ask(genderQuestion, signal);
    const hasChildren = await ask(childrenQuestion, signal);
    const hasOtherAnimals = await ask(otherPetsQuestion, signal);
    const experience = hasOtherAnimals ? await ask(experienceQuestion, signal) : null;
    const activity = await ask(activityQuestion, signal);
    const housing = await ask(housingQuestion, signal);
    const shelter = await ask({
        text: 'В какой приют вам удобно приехать?',
        friendText: 'В какой приют тебе удобно приехать?',
        options: shelters.map(value => ({ label: shelterLabel(value), value })),
    }, signal);

    const { animals, conversation } = await withRequest(async () => {
        const catalog = await api.animals();
        const conversation = await api.createConversation({
            shelter: shelter.id,
            purpose,
            species,
            housing,
            communication_style: communicationStyle,
            questionnaire: {
                gender,
                has_children: hasChildren,
                has_other_animals: hasOtherAnimals,
                had_animals_before: experience,
                activity,
            },
        });
        sessionId = conversation.session_id;
        return { animals: catalog, conversation };
    });

    setStep('stepPodb');
    setMessageMode('chat');
    const matches = animals.filter(animal => matchesAnimal(animal, shelter.id, species, gender));
    if (!matches.length) {
        botSay('В этом приюте сейчас нет питомцев по выбранному виду и полу. Можно задать вопрос или начать подбор заново.');
        return;
    }
    let suggestions = matches;
    if (conversation.assistant_enabled) {
        const pending = botSay('ИИ-помощник подбирает питомцев…');
        try {
            const reply = await withRequest(() => api.sendMessage(
                conversation.session_id, 'Помоги подобрать питомца по моей анкете.',
            ));
            const matchingIds = new Set(matches.map(animal => animal.id));
            const recommended = reply.animals.filter(animal => matchingIds.has(animal.id));
            if (recommended.length) suggestions = recommended;
            botSay(reply.bot_message.content);
        } catch (error) {
            botSay(errorMessage(error));
        } finally {
            pending.remove();
        }
    }
    botSay('Вот кто сейчас ищет дом в выбранном приюте.', 'Вот кто ищет дом в этом приюте.');
    const animal = await chooseAnimal(suggestions, signal);
    await showAnimalActions(animal, shelter, purpose, signal);
}

function shelterLabel(shelter: Shelter) {
    return [shelter.name, shelter.city, shelter.address].filter(Boolean).join(' · ');
}

async function searchByName(name: string, signal: AbortSignal) {
    const [animals, shelters] = await withRequest(() => Promise.all([api.animals(), api.shelters()]));
    addMessage(name, 'user');
    const normalize = (value: string) => value.trim().toLocaleLowerCase('ru');
    const matches = animals
        .filter(animal => normalize(animal.name) === normalize(name))
        .sort((first, second) => Number(Boolean(second.photo)) - Number(Boolean(first.photo)));
    if (!matches.length) {
        botSay(
            `Питомца с кличкой «${name}» сейчас нет в каталоге. Проверьте кличку и попробуйте ещё раз.`,
            `Не нашёл в каталоге питомца с кличкой «${name}». Проверь, правильно ли она написана.`,
        );
        return;
    }

    setMessageMode(null);
    setStep('stepPodb');
    let animal = matches[0];
    let card: HTMLElement | undefined;
    if (matches.length === 1) {
        card = petCard(animal);
        chatLog.append(card);
    } else {
        botSay(
            'В каталоге несколько питомцев с такой кличкой. Кого вы ищете?',
            'Нашёл несколько питомцев с такой кличкой. Кого из них ты ищешь?',
        );
        animal = await chooseAnimal(matches, signal);
    }
    const shelter = shelters.find(item => item.id === animal.shelter);
    const nextAction = showAnimalActions(animal, shelter, 'undecided', signal);
    if (card) revealChatItem(card);
    await nextAction;
}

async function showAnimalActions(
    animal: CatalogAnimal,
    shelter: Shelter | undefined,
    purpose: ConversationInput['purpose'],
    signal: AbortSignal,
) {
    if (animal.status === 'adopted') {
        botSay(`${animal.name} уже нашёл дом. Можно поискать другого питомца.`);
        setMessageMode('name');
        return;
    }

    if (shelter) botSay(`Приют: ${shelterLabel(shelter)}.`);
    else botSay('В карточке этого питомца пока не указан приют.');

    type Action = 'visit' | 'decline' | 'guardianship' | 'message';
    const options: Option<Action>[] = [];
    if (shelter) {
        options.push({ label: 'Хочу приехать', value: 'visit' });
        if (!sessionId) options.push({ label: 'Задать вопрос', value: 'message' });
    }
    if (purpose !== 'adoption') {
        if (animal.guardianship_slots > 0) options.push({ label: 'Оформить опеку', value: 'guardianship' });
        else botSay('У этого питомца уже пять опекунов. Все места заняты.');
    }
    options.push({ label: 'Продолжить поиск', value: 'decline' });

    const action = await ask({
        text: 'Что хотите сделать дальше?',
        friendText: 'Что хочешь сделать дальше?',
        options,
    }, signal);
    if (action === 'visit' && shelter) {
        setStep('stepOfr');
        const contact = shelter.phone ? `по телефону ${shelter.phone}` : `«${shelter.name}»`;
        botSay(
            `Чтобы договориться о визите, свяжитесь с приютом ${contact}.`,
            `Если хочешь приехать, свяжись с приютом ${contact} и договорись о времени.`,
        );
    } else if (action === 'guardianship') {
        const completed = await registerGuardianship(animal);
        if (!completed && !signal.aborted) {
            const catalog = await withRequest(api.animals);
            const current = catalog.find(item => item.id === animal.id);
            if (current) await showAnimalActions(current, shelter, purpose, signal);
        }
    } else if (action === 'message' && shelter) {
        await openPetConversation(animal, shelter, signal);
    } else {
        await showStartOptions(signal);
    }
}

async function registerGuardianship(animal: CatalogAnimal) {
    const completed = await openSubscription(animal);
    void refreshCatalog();
    if (!completed) return false;

    setStep('stepOfr');
    botSay(
        `Тестовая оплата прошла успешно. Опека над питомцем «${animal.name}» оформлена.`,
        `Тестовая оплата прошла успешно. Теперь ты опекун питомца «${animal.name}».`,
    );
    void showGuardianships();
    return true;
}

async function openPetConversation(animal: Animal, shelter: Shelter, signal: AbortSignal) {
    const purpose = await ask(purposeQuestion, signal);
    const housing = await ask(housingQuestion, signal);
    const conversation = await withRequest(() => api.createConversation({
        shelter: shelter.id,
        purpose,
        species: animal.species,
        housing,
        communication_style: communicationStyle,
    }));
    sessionId = conversation.session_id;
    setMessageMode('chat');
    botSay('Напишите, что хотите узнать.', 'Напиши, что хочешь узнать.');
    messageInput.focus();
}

messageForm.addEventListener('submit', async event => {
    event.preventDefault();
    const text = messageInput.value.trim();
    if (isBusy() || !text) return;
    const signal = dialog.signal;
    try {
        if (messageMode === 'name') {
            messageInput.value = '';
            await searchByName(text, signal);
        } else if (messageMode === 'chat' && sessionId) {
            const id = sessionId;
            const reply = await withRequest(() => api.sendMessage(id, text));
            messageInput.value = '';
            addMessage(reply.user_message.content, 'user');
            botSay(reply.bot_message.content);
            for (const animal of reply.animals) {
                chatLog.append(petCard(animal));
            }
            const firstCard = reply.animals.length && chatLog.children.item(chatLog.children.length - reply.animals.length);
            if (firstCard instanceof HTMLElement) revealChatItem(firstCard);
        }
    } catch (error) {
        if (signal.aborted) return;
        botSay(errorMessage(error));
        if (messageMode === 'name') messageInput.value = text;
        if (!messageMode) await showStartOptions(signal);
    }
});

export function clearChat() {
    dialog.abort();
    sessionId = null;
    setMessageMode(null);
    chatLog.replaceChildren();
}
