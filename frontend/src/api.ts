export interface Registration {
    first_name: string;
    last_name: string;
    phone: string;
    city: string;
    email: string;
    telegram: string;
    username: string;
    password: string;
}

export interface Shelter {
    id: number;
    name: string;
    city: string;
    address: string;
    phone: string;
}

export interface Animal {
    id: number;
    name: string;
    shelter: number | null;
    shelter_name: string | null;
    species: 'cat' | 'dog';
    breed: string;
    age: string | null;
    description: string;
    gender: string;
    coat_color: string;
    coat_color_source: 'shelter' | 'photo' | null;
    status: 'available' | 'adopted';
    photo: string | null;
}

export interface CatalogAnimal extends Animal {
    guardianship_slots: number;
}

export interface Guardianship {
    id: number;
    animal: Animal;
    status: 'active';
    created_at: string;
}

export interface ConversationInput {
    selected_animal?: number;
    shelter: number;
    purpose: 'adoption' | 'guardianship' | 'undecided';
    species: Animal['species'] | 'any';
    housing: 'apartment' | 'house';
    communication_style: 'friend' | 'consultant';
    questionnaire?: {
        gender: 'male' | 'female' | 'any';
        has_children: boolean;
        has_other_animals: boolean;
        had_animals_before: boolean | null;
        activity: 'active' | 'calm';
    };
}

interface SessionStatus {
    access: string | null;
    csrfToken: string;
}

interface ChatMessage {
    id: number;
    role: 'user' | 'assistant' | 'operator';
    content: string;
    created_at: string;
}

const defaultApiUrl = import.meta.env.DEV ? 'http://localhost:8000' : window.location.origin;
const apiUrl = (import.meta.env.VITE_API_URL || defaultApiUrl).replace(/\/+$/, '');
const sessionPath = '/api/auth/session/';
let accessToken: string | null = null;
let csrfToken: string | null = null;
let sessionRequest: Promise<boolean> | null = null;

const fieldLabels: Readonly<Record<string, string>> = {
    username: 'Логин',
    password: 'Пароль',
    first_name: 'Имя',
    last_name: 'Фамилия',
    email: 'Почта',
    phone: 'Телефон',
    city: 'Город',
    telegram: 'Telegram',
};

function describeError(body: unknown, status: number): string {
    if (typeof body === 'object' && body !== null) {
        for (const [field, value] of Object.entries(body)) {
            const message = Array.isArray(value) ? value.find(item => typeof item === 'string') : value;
            if (typeof message === 'string') {
                const label = fieldLabels[field];
                return label ? `${label}: ${message}` : message;
            }
        }
    }
    return `Сервер вернул ошибку ${status}. Попробуйте ещё раз.`;
}

interface RequestOptions {
    data?: object;
    method?: 'DELETE';
    authenticated?: boolean;
    timeout?: number;
}

async function request<T>(path: string, options: RequestOptions = {}, retry = true): Promise<T> {
    const { data, authenticated = false, timeout = 12_000 } = options;
    const method = options.method ?? (data ? 'POST' : 'GET');
    const browserSession = path === sessionPath;
    const headers = new Headers({ Accept: 'application/json' });
    if (data) headers.set('Content-Type', 'application/json');
    if (authenticated && accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
    if (browserSession && method !== 'GET' && csrfToken) headers.set('X-CSRFToken', csrfToken);

    let response: Response;
    try {
        response = await fetch(`${apiUrl}${path}`, {
            method,
            credentials: browserSession ? 'include' : 'omit',
            headers,
            body: data ? JSON.stringify(data) : undefined,
            signal: AbortSignal.timeout(timeout),
        });
    } catch {
        throw new Error('Не удалось связаться с сервером. Попробуйте ещё раз.');
    }

    if (response.status === 401 && authenticated) {
        if (retry && await restoreSession()) {
            return request<T>(path, options, false);
        }
        throw new Error('Сессия завершилась. Войдите в аккаунт снова.');
    }

    const body: unknown = await response.json().catch(() => null);
    if (!response.ok) {
        throw new Error(describeError(body, response.status));
    }
    return body as T;
}

function restoreSession() {
    sessionRequest ??= request<SessionStatus>(sessionPath)
        .then(session => {
            csrfToken = session.csrfToken;
            accessToken = session.access;
            return Boolean(accessToken);
        })
        .finally(() => { sessionRequest = null; });
    return sessionRequest;
}

export const api = {
    register: (data: Registration) => request<Omit<Registration, 'password'>>('/api/auth/register/', { data }),
    restoreSession,
    async login(username: string, password: string) {
        if (!csrfToken) await restoreSession();
        const result = await request<{ access: string }>(sessionPath, { data: { username, password } });
        accessToken = result.access;
    },
    async signOut() {
        await request<void>(sessionPath, { method: 'DELETE' });
        accessToken = null;
    },
    shelters: () => request<Shelter[]>('/api/chat/shelters/'),
    animals: () => request<CatalogAnimal[]>('/api/animals/'),
    guardianships: () => request<Guardianship[]>('/api/auth/my-guardianships/', { authenticated: true }),
    createConversation: (data: ConversationInput) =>
        request<{ session_id: string; assistant_enabled: boolean }>('/api/chat/conversations/', { data, authenticated: true }),
    sendMessage: (sessionId: string, content: string) =>
        request<{ user_message: ChatMessage; bot_message: ChatMessage; animals: CatalogAnimal[] }>(
            `/api/chat/conversations/${sessionId}/messages/`,
            { data: { content }, authenticated: true, timeout: 25_000 },
        ),
    registerGuardianship: (animalId: number) =>
        request<Guardianship>('/api/auth/guardianships/', {
            data: { animal_id: animalId },
            authenticated: true,
        }),
};
