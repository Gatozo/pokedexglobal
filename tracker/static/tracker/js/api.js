/**
 * Pokédex Global - Módulo de Red y API (api.js)
 * Manejo de CSRF tokens y peticiones asíncronas hacia los endpoints de Django.
 */

export function getCsrfToken() {
    const input = document.querySelector('[name=csrfmiddlewaretoken]');
    return input ? input.value : '';
}

export async function postJson(url, data) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken(),
        },
        body: JSON.stringify(data)
    });
    if (!response.ok) {
        throw new Error(`HTTP error ${response.status} en ${url}`);
    }
    return await response.json();
}
