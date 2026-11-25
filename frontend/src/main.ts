import './styles/widget.css';
import './styles/account.css';
import './styles/pet-card.css';
import './styles/catalog.css';

import { api } from './api';
import { hideAccount, showAccount, showChatTab, showGuardianships } from './account';
import { isSignedIn, resetAuth, setupAuth, showLogin } from './auth';
import { refreshCatalog, setupCatalog } from './catalog';
import { clearChat, startChat } from './chat';
import { openChat } from './chat-window';
import { element, setStep } from './dom';
import { errorMessage, withRequest } from './request-state';
import { openSubscription } from './subscription';

let afterLogin: (() => void) | null = null;

const sessionReady = setupAuth(() => {
    showAccount();
    void startChat();
    const action = afterLogin;
    afterLogin = null;
    action?.();
});

async function withAccount(action: () => void) {
    await sessionReady;
    if (isSignedIn()) action();
    else {
        afterLogin = action;
        openChat();
    }
}

setupCatalog(animal => {
    void withAccount(() => {
        void (async () => {
            const completed = await openSubscription(animal);
            void refreshCatalog();
            if (completed) {
                openChat();
                void showGuardianships();
            }
        })();
    });
});

element('#openWards', HTMLButtonElement).addEventListener('click', () => {
    openChat();
    void withAccount(() => { void showGuardianships(); });
});

element('#restartBot', HTMLButtonElement).addEventListener('click', () => {
    if (isSignedIn()) {
        showChatTab();
        void startChat();
    } else {
        resetAuth();
    }
});

const sessionStatus = element('#sessionStatus', HTMLParagraphElement);
element('#signOut', HTMLButtonElement).addEventListener('click', async () => {
    sessionStatus.textContent = '';
    try {
        await withRequest(api.signOut);
    } catch (error) {
        sessionStatus.textContent = errorMessage(error);
        return;
    }
    clearChat();
    hideAccount();
    setStep('stepReg');
    showLogin();
});

element('#closeChat', HTMLButtonElement).addEventListener('click', () => {
    afterLogin = null;
});
