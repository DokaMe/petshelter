import { element } from './dom';

const chatOpen = element('#btnToOpenChat', HTMLButtonElement);
const chat = element('#chatCont', HTMLElement);
const chatHeader = element('.botHeader', HTMLDivElement);
const chatClose = element('#closeChat', HTMLButtonElement);
const fullScreen = element('#fullScreen', HTMLButtonElement);

function setFullscreen(open: boolean) {
    chat.style.cssText = '';
    chat.classList.toggle('fullscreen', open);
    const label = open ? 'Свернуть' : 'Развернуть';
    fullScreen.title = label;
    fullScreen.setAttribute('aria-label', label);
    fullScreen.setAttribute('aria-pressed', String(open));
}

function setChatOpen(open: boolean) {
    chat.classList.toggle('botHidden', !open);
    chatOpen.setAttribute('aria-expanded', String(open));
}

export function openChat() {
    setChatOpen(true);
}

chatOpen.addEventListener('click', openChat);
chatClose.addEventListener('click', () => {
    setFullscreen(false);
    setChatOpen(false);
    chatOpen.focus();
});
fullScreen.addEventListener('click', () => setFullscreen(!chat.classList.contains('fullscreen')));
const mobileLayout = window.matchMedia('(max-width: 780px)');
mobileLayout.addEventListener('change', () => setFullscreen(false));

let dragOffset: { x: number; y: number } | null = null;
chatHeader.addEventListener('mousedown', event => {
    if (event.button !== 0 || mobileLayout.matches || chat.classList.contains('fullscreen')) return;
    if (event.target instanceof Element && event.target.closest('button')) return;

    const rect = chat.getBoundingClientRect();
    dragOffset = { x: event.clientX - rect.left, y: event.clientY - rect.top };
    chat.style.left = `${rect.left}px`;
    chat.style.top = `${rect.top}px`;
    chat.style.right = 'auto';
    chat.style.bottom = 'auto';
    chat.style.transition = 'none';
    event.preventDefault();
});
document.addEventListener('mousemove', event => {
    if (!dragOffset) return;
    const x = Math.max(0, Math.min(event.clientX - dragOffset.x, window.innerWidth - chat.offsetWidth));
    const y = Math.max(0, Math.min(event.clientY - dragOffset.y, window.innerHeight - chat.offsetHeight));
    chat.style.left = `${x}px`;
    chat.style.top = `${y}px`;
});
document.addEventListener('mouseup', () => {
    if (!dragOffset) return;
    dragOffset = null;
    chat.style.transition = '';
});
