import { api } from './api';
import type { Registration } from './api';
import { element } from './dom';
import { errorMessage, isBusy, withRequest } from './request-state';

const authForm = element('#regForm', HTMLFormElement);
const authTitle = element('#authTitle', HTMLHeadingElement);
const authIntro = element('#authIntro', HTMLParagraphElement);
const authFields = element('#registrationFields', HTMLFieldSetElement);
const authError = element('#authError', HTMLParagraphElement);
const authSubmit = element('#regSubmit', HTMLButtonElement);
const authToggle = element('#authToggle', HTMLButtonElement);
const passwordInput = element('[name=password]', HTMLInputElement);

let authMode: 'register' | 'login' = 'register';

function showAuthError(message: string) {
    authError.textContent = message;
    authError.classList.toggle('hidden', !message);
}

function setAuthMode(mode: typeof authMode) {
    authMode = mode;
    const login = mode === 'login';
    authTitle.textContent = login ? 'Войдите в аккаунт' : 'Давайте познакомимся!';
    authIntro.classList.toggle('hidden', login);
    authFields.classList.toggle('hidden', login);
    authFields.disabled = login;
    passwordInput.autocomplete = login ? 'current-password' : 'new-password';
    passwordInput.minLength = login ? 0 : 8;
    passwordInput.placeholder = login ? 'Пароль *' : 'Пароль (от 8 символов) *';
    authSubmit.textContent = login ? 'Войти' : 'Зарегистрироваться';
    authToggle.textContent = login ? 'Создать аккаунт' : 'Уже есть аккаунт? Войти';
    showAuthError('');
}

export function setupAuth(onLogin: () => void) {
    function finishLogin() {
        passwordInput.value = '';
        authForm.classList.add('hidden');
        onLogin();
    }

    authToggle.addEventListener('click', () => {
        setAuthMode(authMode === 'register' ? 'login' : 'register');
        passwordInput.value = '';
    });

    authForm.addEventListener('submit', async event => {
        event.preventDefault();
        if (isBusy()) return;
        const form = new FormData(authForm);
        const read = (name: keyof Registration) => String(form.get(name) ?? '').trim();
        const username = read('username');
        const password = passwordInput.value;
        let registered = false;

        showAuthError('');
        try {
            await withRequest(async () => {
                if (authMode === 'register') {
                    const data: Registration = {
                        username,
                        password,
                        first_name: read('first_name'),
                        last_name: read('last_name'),
                        phone: read('phone'),
                        city: read('city'),
                        email: read('email'),
                        telegram: read('telegram'),
                    };
                    if (!data.first_name || !data.last_name || !data.phone || !data.city) {
                        throw new Error('Заполните обязательные поля.');
                    }
                    await api.register(data);
                    registered = true;
                }
                await api.login(username, password);
            });
        } catch (error) {
            if (registered) {
                setAuthMode('login');
                showAuthError(`Аккаунт создан. Войдите вручную. ${errorMessage(error)}`);
            } else {
                showAuthError(errorMessage(error));
            }
            return;
        }

        finishLogin();
    });

    return withRequest(api.restoreSession)
        .then(authenticated => {
            if (authenticated) finishLogin();
        })
        .catch(error => showAuthError(errorMessage(error)));
}

export function resetAuth() {
    authForm.reset();
    showAuthError('');
}

export function showLogin() {
    authForm.classList.remove('hidden');
    setAuthMode('login');
}

export function isSignedIn() {
    return authForm.classList.contains('hidden');
}
