import { smartapp } from './smartapp.js';

export const handler = async (event, _context) => {
    const body = typeof event.body === 'string' ? JSON.parse(event.body) : event.body;

    return new Promise((resolve, reject) => {
        const req = { body };
        const res = {
            status: (code) => ({
                json: (data) => resolve({
                    statusCode: code,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                }),
                send: (data) => resolve({
                    statusCode: code,
                    headers: { 'Content-Type': 'application/json' },
                    body: typeof data === 'string' ? data : JSON.stringify(data),
                }),
            }),
            json: (data) => resolve({
                statusCode: 200,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data),
            }),
        };
        smartapp.handleHttpCallback(req, res);
    });
};
