import { api } from './api';
import { element } from './dom';
import { petCard } from './pet-card';
import { errorMessage, isBusy, withRequest } from './request-state';

const account = element('#account', HTMLElement);
const chatTab = element('#chatTab', HTMLButtonElement);
const guardianshipsTab = element('#guardianshipsTab', HTMLButtonElement);
const chatPanel = element('#chatPanel', HTMLElement);
const guardianshipsPanel = element('#guardianshipsPanel', HTMLElement);
const guardianshipList = element('#guardianshipList', HTMLDivElement);
const statusMessage = element('#guardianshipStatus', HTMLParagraphElement);
const retry = element('#guardianshipRetry', HTMLButtonElement);
const sidebar = element('.sidebar', HTMLElement);
const dateFormat = new Intl.DateTimeFormat('ru-RU', { dateStyle: 'long' });

function selectTab(tab: HTMLButtonElement) {
    const showChat = tab === chatTab;
    for (const item of [chatTab, guardianshipsTab]) {
        const selected = item === tab;
        item.setAttribute('aria-selected', String(selected));
        item.tabIndex = selected ? 0 : -1;
    }
    chatPanel.classList.toggle('hidden', !showChat);
    guardianshipsPanel.classList.toggle('hidden', showChat);
    sidebar.classList.toggle('hidden', !showChat);
}

export function showChatTab() {
    selectTab(chatTab);
}

export async function showGuardianships() {
    if (isBusy()) return;
    selectTab(guardianshipsTab);
    guardianshipsTab.focus();
    guardianshipList.replaceChildren();
    statusMessage.textContent = 'Загружаем подопечных…';
    guardianshipList.setAttribute('aria-busy', 'true');
    retry.classList.add('hidden');

    try {
        const registrations = await withRequest(api.guardianships);
        statusMessage.textContent = registrations.length
            ? ''
            : 'Здесь появятся питомцы, на которых вы оформите опеку.';
        for (const registration of registrations) {
            guardianshipList.append(petCard(registration.animal, {
                details: `Опека с ${dateFormat.format(new Date(registration.created_at))}`,
            }));
        }
    } catch (error) {
        statusMessage.textContent = errorMessage(error);
        retry.classList.remove('hidden');
    } finally {
        guardianshipList.removeAttribute('aria-busy');
    }
}

export function showAccount() {
    account.classList.remove('hidden');
    showChatTab();
}

export function hideAccount() {
    account.classList.add('hidden');
    guardianshipList.replaceChildren();
    showChatTab();
}

chatTab.addEventListener('click', showChatTab);
guardianshipsTab.addEventListener('click', () => { void showGuardianships(); });
retry.addEventListener('click', () => { void showGuardianships(); });
for (const tab of [chatTab, guardianshipsTab]) {
    tab.addEventListener('keydown', event => {
        if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        event.preventDefault();
        const nextTab = event.key === 'Home' || (event.key !== 'End' && tab === guardianshipsTab)
            ? chatTab : guardianshipsTab;
        nextTab.click();
        nextTab.focus();
    });
}
